import csv
import os
import ast

import pandas as pd
from loguru import logger

from src.config import Config as config
from src.utils.query_templates import all_issues
from src.utils.graphql import query_graphql
from src.utils.datetime_parser import parse_datetime

def get_all_issues(owner_name, repo_name):
    """获取指定仓库的所有issue并存储到 CSV 文件中."""
    # 初始查询模板
    query_template = all_issues

    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_issues.csv"

    if os.path.exists(csv_file):
        return csv_file

    cursor = None
    issues = []

    while True:
        # 构建查询
        if cursor is None:
            tem_cursor = ""
        else:
            tem_cursor = ', after: "%s"' % cursor

        query_string = query_template % (owner_name, repo_name, tem_cursor)

        # 执行查询
        response = query_graphql(query_string)

        # 解析响应
        edges = response["data"]["repository"]["issues"]["edges"]
        page_info = response["data"]["repository"]["issues"]["pageInfo"]

        for edge in edges:
            issue = edge["node"]
            issues.append([
                issue["title"],
                [i["node"]["name"] for i in issue["labels"]["edges"]],
                issue["labels"]["totalCount"],
                issue["createdAt"],
                issue["closedAt"],
                issue["state"],
            ])

        logger.debug(f"{csv_file} cursor at {cursor}")
        # 检查是否还有下一页
        if not page_info["hasNextPage"]:
            break

        # 更新游标进行下一次查询
        cursor = page_info["endCursor"]

    df = pd.DataFrame(issues, columns=["title",
                                       "issue_labels",
                                       "issue_label_count",
                                       "createdAt",
                                       "closedAt",
                                       "state"])

    # 写入 CSV 文件
    df.to_csv(csv_file, index=False, encoding='utf-8')
    logger.info(f"Write {len(issues)} issues to {csv_file}")

    return csv_file

def get_sliced_issues(owner_name, repo_name, slice_rules):
    # 读取 CSV 文件
    df = pd.read_csv(get_all_issues(owner_name, repo_name))

    # 转换 createdAt 和 closedAt 列
    df['createdAt'] = df['createdAt'].apply(parse_datetime)
    df['closedAt'] = df['closedAt'].apply(lambda x: None if pd.isna(x) else parse_datetime(x))

    # 转换 issue_labels 列为列表
    df['issue_labels'] = df['issue_labels'].apply(lambda x: ast.literal_eval(x))

    # 转换 issue_label_count 列为整数
    df['issue_label_count'] = df['issue_label_count'].astype(int)
    
    # 存储每个切片的数量
    created_counts = []
    lable_counts = []
    
    for start_date, end_date in slice_rules:
        filter = df[(df['createdAt'] >= start_date) & (df['createdAt'] < end_date)]
        count = filter.shape[0]
        lable = filter['issue_label_count'].sum()
        created_counts.append(count)
        lable_counts.append(int(lable))

    # 存储每个切片的数量
    close_counts = []
    
    for start_date, end_date in slice_rules:
        count = df[(df['closedAt'] >= start_date) & (df['closedAt'] < end_date)].shape[0]
        close_counts.append(count)

    return created_counts, close_counts, lable_counts

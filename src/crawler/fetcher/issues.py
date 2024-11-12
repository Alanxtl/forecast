import csv
from datetime import datetime, timedelta
import os
import pandas as pd
import ast
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
            issues.append({
                "title": issue["title"],
                "issue_labels": [i["node"]["name"] for i in issue["labels"]["edges"]],
                "issue_label_count": issue["labels"]["totalCount"],
                "createdAt": issue["createdAt"],
                "closedAt": issue["closedAt"],
                "state": issue["state"],
            })

        logger.debug(f"{csv_file} cursor at {cursor}")
        # 检查是否还有下一页
        if not page_info["hasNextPage"]:
            break

        # 更新游标进行下一次查询
        cursor = page_info["endCursor"]

    # 写入 CSV 文件
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        try:
            writer = csv.DictWriter(file, fieldnames=["title",
                                                    "issue_labels",
                                                    "issue_label_count",
                                                    "createdAt",
                                                    "closedAt",
                                                    "state",
            ])
            writer.writeheader()  # 写入表头
            writer.writerows(issues)  # 写入所有提交信息
        finally:
            file.close()

    logger.info(f"write {len(issues)} issues to {csv_file}")

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
    
    for start_date, end_date in slice_rules:
        count = df[(df['createdAt'] >= start_date) & (df['createdAt'] < end_date)].shape[0]
        created_counts.append(count)

    # 存储每个切片的数量
    close_counts = []
    
    for start_date, end_date in slice_rules:
        count = df[(df['closedAt'] >= start_date) & (df['closedAt'] < end_date)].shape[0]
        close_counts.append(count)

import csv
from datetime import datetime, timedelta
from loguru import logger

from src.config import Config as config
from src.crawler.query_templates import all_issues
from src.crawler.graphql import query_graphql
from src.utils.datetime_parser import parse_datetime

def get_all_issues(owner_name, repo_name):
    """获取指定仓库的所有issue并存储到 CSV 文件中."""
    # 初始查询模板
    query_template = all_issues

    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_issues.csv"

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

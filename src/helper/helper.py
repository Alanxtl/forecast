import sys
import os
import csv
from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, f'../crawler'))

import graphql

def get_all_commits(owner_name, repo_name):
    """获取指定仓库的所有提交信息并存储到 CSV 文件中."""
    # 初始查询模板
    query_template = """
    {
        repository(owner: "%s", name: "%s") {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100%s) {
                            edges {
                                node {
                                    author {
                                        name
                                        email
                                    }
                                    additions
                                    deletions
                                    changedFilesIfAvailable
                                    committedDate
                                    message
                                    oid
                                }
                            }
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                    }
                }
            }
        }
    }
    """

    csv_file = f"./data/{owner_name}_{repo_name}.csv"

    cursor = None
    commits = []

    while True:
        # 构建查询
        if cursor is None:
            tem_cursor = ""
        else:
            tem_cursor = ', after: "%s"' % cursor

        query_string = query_template % (owner_name, repo_name, tem_cursor)

        # 执行查询
        response = graphql.query(query_string)

        # 解析响应
        edges = response["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
        page_info = response["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]

        for edge in edges:
            commit = edge["node"]
            commits.append({
                "oid": commit["oid"],
                "committedDate": commit["committedDate"],
                "message": commit["message"],
                "author_name": commit["author"]["name"],
                "author_email": commit["author"]["email"],
                "additions": commit["additions"],
                "deletions": commit["deletions"],
                "changedFilesIfAvailable": commit["changedFilesIfAvailable"],
                # "file": commit["file"],
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
            writer = csv.DictWriter(file, fieldnames=["oid",
                                                    "committedDate",
                                                    "message",
                                                    "author_name",
                                                    "author_email",
                                                    "additions",
                                                    "deletions",
                                                    "changedFilesIfAvailable",
                                                    # "file"
            ])
            writer.writeheader()  # 写入表头
            writer.writerows(commits)  # 写入所有提交信息
        finally:
            file.close()

    logger.info(f"write {len(commits)} commits to {csv_file}")

def get_last_commit_date(owner_name, repo_name):
    csv_file = f"./data/{owner_name}_{repo_name}.csv"

    if not os.path.exists(csv_file):
        get_all_commits(owner_name, repo_name)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            last_row = None
            for row in reader:
                last_row = row

            if last_row is None:
                return None
            else:
                return last_row["committedDate"]
        finally:
            file.close()

if __name__ == "__main__":
    print(get_last_commit_date("XS-MLVP", "env-xs-ov-00-bpu"))

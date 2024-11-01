import datetime
import sys
import os
import csv
from datetime import datetime, timedelta
from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, f'../crawler'))
sys.path.append(os.path.join(current_dir, f'../'))

import config as config
import graphql
from .utils import parse_datetime
from .query_templates import all_commits

def get_all_commits(owner_name, repo_name):
    """获取指定仓库的所有提交信息并存储到 CSV 文件中."""
    # 初始查询模板
    query_template = all_commits

    csv_file = config.Config.get_config()["data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

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
    csv_file = config.Config.get_config()["data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

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

def get_m_months_data_given_start_date(owner_name, repo_name, start_date: datetime, m: int = int(config.Config.get_config()["window_size"])):
    csv_file = config.Config.get_config()["data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    if not os.path.exists(csv_file):
        get_all_commits(owner_name, repo_name)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            commits = []
            for row in reader:
                date = parse_datetime(row["committedDate"])
                if date < start_date:
                    break
                if date <= start_date + timedelta(days = 30 * m):
                    commits.append(row)
            return commits
        finally:
            file.close()

def slice_all_commit_data(owner_name, repo_name, window_size: int = int(config.Config.get_config()["window_size"]), step_length: int = int(config.Config.get_config()["step_size"])):
    csv_file = config.Config.get_config()["data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    if not os.path.exists(csv_file):
        get_all_commits(owner_name, repo_name)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            commits = list(reader)
        finally:
            file.close()

    slices = []
    total_commits = len(commits)
    window_days = window_size * 30
    step_days = step_length * 30

    # reverse
    current_ptr = total_commits - 1

    while current_ptr >= 0:
        slice_commits = []
        current_start_date = parse_datetime(commits[current_ptr]["committedDate"])
        current_end_date = current_start_date + timedelta(days = window_days)
        next_date = current_start_date + timedelta(days = step_days)
        next_ptr = current_ptr

        while parse_datetime(commits[current_ptr]["committedDate"]) < current_end_date and current_ptr >= 0:
            if parse_datetime(commits[current_ptr]["committedDate"]) < next_date:
                next_ptr = current_ptr - 1
                # print("next =", next_ptr)

            slice_commits.append(commits[current_ptr])

            current_ptr -= 1

        slices.append(slice_commits)
        current_ptr = next_ptr

    return slices

if __name__ == "__main__":
    print(get_last_commit_date("XS-MLVP", "env-xs-ov-00-bpu"))

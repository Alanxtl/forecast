import datetime
import time
import sys
import os
import csv
from datetime import datetime, timedelta
from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, f'../../../helper'))
sys.path.append(os.path.join(current_dir, f'../../../'))
sys.path.append(os.path.join(current_dir, f'../'))

import config as config
from graphql import query_graphql
from utils import parse_datetime
from query_templates import all_commits

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
        response = query_graphql(query_string)

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

def get_specific_developer_s_all_commit_on_specific_repo(owner_name, repo_name, name):

    csv_file = config.Config.get_config()["data_path"] + f"/{owner_name}_{repo_name}_commits.csv"
    target_csv_file = config.Config.get_config()["data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"

    if os.path.exists(target_csv_file):
        with open(target_csv_file, mode='r', newline='', encoding='utf-8') as file:
            try:
                reader = csv.DictReader(file)
                commits = list(reader)
            finally:
                file.close()

        return len(commits)

    if not os.path.exists(csv_file):
        get_all_commits(owner_name, repo_name)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            commits = list(reader)
        finally:
            file.close()

    ret = 0

    # 写入 CSV 文件
    with open(target_csv_file, mode='w', newline='', encoding='utf-8') as file:
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
            for i in commits: 
                if i["author_name"] == name:
                    ret += 1
                    writer.writerow(i)  # 写入所有提交信息
        finally:
            file.close()

    logger.info(f"write {ret} commits to {target_csv_file}")

    return ret

def get_specific_developer_s_commit_on_specific_repo_from_to(owner_name, repo_name, name,
                                                             start: str = "2000-01-01", 
                                                             end: str = datetime.now().strftime('%Y-%m-%d')):
    start_time = time.strptime(start, "%Y-%m-%d")
    end_time = time.strptime(end, "%Y-%m-%d")

    target_csv_file = config.Config.get_config()["data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"

    if not os.path.exists(target_csv_file):
        get_specific_developer_s_all_commit_on_specific_repo(owner_name, repo_name, name)
        
    with open(target_csv_file, mode='r', newline='', encoding='utf-8') as file:
        count = 0

        try:
            reader = csv.DictReader(file)
            commits = list(reader)
            check = 1
            for row in commits:
                t = parse_datetime(row['committedDate'])
                if t < end_time and t >= start_time:
                    check = 2
                    count += 1
                elif check == 2:
                    check == 3
                if check == 3:
                    break
        finally:
            file.close()

        return count

if __name__ == "__main__":
    print(get_last_commit_date("Alanxtl", "env-xs-ov-00-bpu", "Alanxtl"))

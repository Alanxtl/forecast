import ast
import re
import datetime
import sys
import os
import csv
from datetime import datetime
from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, f'../../../helper'))
sys.path.append(os.path.join(current_dir, f'../../../'))
sys.path.append(os.path.join(current_dir, f'../'))

import config as config
from graphql import query_api, get_html
from utils import parse_datetime

def get_developer_s_all_repos(name): 
    """获取某人所有的 repo"""
    file = config.Config.get_config()["raw_data_path"] + f"/{name}_s_all_repos.txt"

    if os.path.exists(file):
        with open(file, mode='r', newline='', encoding='utf-8') as file:
            try:
                reader = file.readline()
                all_repos = ast.literal_eval(reader)
            finally:
                file.close()

            return all_repos


    url_repos = 'https://api.github.com/users/{name}/repos'.format(name=name)
    json_data = query_api(url_repos)

    all_repos = [] # repos's name数据存放数组

    try:
        for item in json_data:
            repo = item['name']
            all_repos.append(repo)
    except Exception as e:
        print(e)

    with open(file, mode='w', newline='', encoding='utf-8') as file:
        try:
            file.write(str(all_repos))
        finally:
            file.close()

    return all_repos

def get_developer_s_commits_on_all_repos(name): 
    repos = get_developer_s_all_repos(name)

    sum = 0
    for repo in repos:
        sum += get_developer_s_all_commits_on_specific_repo(name, repo, name)

    return sum

def get_developer_s_all_commits_on_specific_repo(owner_name, repo_name, name):
    csv_file = config.Config.get_config()["raw_data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"

    if os.path.exists(csv_file):
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            try:
                reader = csv.DictReader(file)
                commits = list(reader)

            finally:
                file.close()

            return len(commits)

    rets = []
    for i in range(1, 99999999):
        quert_url = 'https://api.github.com/repos/%s/%s/commits?author=%s&per_page=100&page=%d' % (owner_name, repo_name, name, i)
        response = query_api(quert_url)
        if response == []:
            break
        rets.extend(response)
        logger.debug(f"{csv_file} cursor at {i}")

    commits = []
    for ret in rets:
            commit = ret
            commits.append({
                "sha": commit["sha"],
                "committedDate": commit["commit"]["author"]["date"],
                "message": commit["commit"]["message"],
                "author_name": commit["commit"]["author"]["name"],
                "author_email": commit["commit"]["author"]["email"],
                # "file": commit["file"],
            })

    # 写入 CSV 文件
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        try:
            writer = csv.DictWriter(file, fieldnames=["sha", "committedDate", "message", 
                                                      "author_name", "author_email"])
            writer.writeheader()  # 写入表头
            writer.writerows(commits)  # 写入所有提交信息
        finally:
            file.close()

    logger.info(f"Write {len(commits)} commits to {csv_file}")
    return len(commits)

def get_developer_s_all_commits_on_specific_repo_ranging_from_to(owner_name, repo_name, name,
                                                                 start: str = '2000-01-01', 
                                                                 end: str = datetime.now().strftime('%Y-%m-%d')):
    start_time = datetime.strptime(start, "%Y-%m-%d")
    end_time = datetime.strptime(end, "%Y-%m-%d")

    csv_file = config.Config.get_config()["raw_data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"

    if not os.path.exists(csv_file):
        get_developer_s_all_commits_on_specific_repo(owner_name, repo_name, name)

    # 写入 CSV 文件
    count = 0
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            commits = list(reader)

            for row in commits:
                t = parse_datetime(row["committedDate"])
                if t < end_time and t >= start_time:
                    count += 1
        finally:
            file.close()

    return count

def get_developer_s_commits_on_all_repos_ranging_from_to(name, start: str = '2000-01-01', end: str = datetime.now().strftime('%Y-%m-%d')):
    repos = get_developer_s_all_repos(name)

    sum = 0
    for repo in repos:
        sum += get_developer_s_all_commits_on_specific_repo_ranging_from_to(name, repo, name, start, end)

    return sum

def calc_developers_focuse_rate_on_repo(owner_name, repo_name, name, 
                                        start: str = "2000-01-01", 
                                        end: str = datetime.now().strftime('%Y-%m-%d')):

    commit_on_repo = get_developer_s_all_commits_on_specific_repo_ranging_from_to(owner_name, repo_name, name, start, end)
    all_commit = get_developer_s_commits_on_all_repos_ranging_from_to(name, start, end)

    return commit_on_repo / all_commit, commit_on_repo, all_commit

if __name__ == "__main__":
    print(get_developer_s_commits_on_all_repos_ranging_from_to("Alanxtl", "2024-01-01", "2025-01-01"))

import ast
import os
import re
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from loguru import logger

from src.config import Config as config
from src.utils.api import query_api
from src.utils.datetime_parser import parse_datetime
from src.utils.git_funcs import clone_to_tmp
from src.utils.evo_log_to_csv import convert
from src.utils.repair_git_move import simple, repair

conf = config.get_config()
TMP = conf["temp_path"]

def contains_chinese_or_space(s):
    # 使用正则表达式检测中文字符或空格
    pattern = re.compile(r'[\u4e00-\u9fff\s]')
    return bool(pattern.search(s))

def get_developer_s_all_repos(name): 
    """获取某人所有的 repo"""
    file = config.get_config()["raw_data_path"] + f"/{name}_s_all_repos.txt"

    if os.path.exists(file):
        with open(file, mode='r', newline='', encoding='utf-8') as file:
            reader = file.readline()
            all_repos = ast.literal_eval(reader)

            return all_repos


    url_repos = r'https://api.github.com/users/' + name + r'/repos'
    json_data = query_api(url_repos)

    all_repos = [] # repos's name数据存放数组

    try:
        for item in json_data:
            repo = item['name']
            owner_name, repo_name = check_fork(name, repo)
            all_repos.append(f"{owner_name}/{repo_name}")
    except Exception as e:
        raise Exception(e)

    with open(file, mode='w', newline='', encoding='utf-8') as file:
        file.write(str(all_repos))

    return all_repos

def write_git_log_to_file_author(owner_name, repo_name, name):
    path_to_repo = r"https://github.com/" + f"{owner_name}/{repo_name}" + r".git"
    
    p = Path(clone_to_tmp(path_to_repo))

    outfile = os.path.join(TMP, p.name + "_evo.log")

    cmd = (
        f"git -C {p} log "
        r'--pretty=format:"\"%H\",\"%an\",\"%ae\",\"%cn\",\"%ce\",\"%aI\",\"%f\"" '
        f"--date=short --numstat > {outfile}"
    )

    subprocess.run(cmd, shell=True)

    return outfile

def check_fork(owner_name, repo_name):
    url = f"https://api.github.com/repos/{owner_name}/{repo_name}"
    json_data = query_api(url)
    if json_data["fork"]:
        return json_data["parent"]["owner"]["login"], json_data["parent"]["name"]
    else:
        return owner_name, repo_name

def get_developer_s_all_commits_on_specific_repo(owner_name, repo_name, name, name_set, email_set):
    csv_file = conf["raw_data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    if os.path.exists(csv_file):
        return csv_file

    evo_log = write_git_log_to_file_author(owner_name, repo_name, name)
    evo_log = convert(evo_log, csv_file)
    evo_log = repair(evo_log)
    
    to_file = config.get_config()["raw_data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"
    evo_log = simple(to_file)
    
    df = pd.read_csv(evo_log, parse_dates=["date"], na_values=["-", "", "\"-\""])

    # 过滤出指定开发者的提交
    df = df[(df["author_email"].isin(email_set)) | 
            (df["committer_email"].isin(email_set)) |
            (df["author_name"].isin(name_set)) |
            (df["committer_name"].isin(name_set))]
    
    df.to_csv(evo_log, index=False)
    
    logger.info(f"Write {len(df)} commits to {evo_log}")

    return evo_log

def get_developer_s_all_alias(name):
    """获取某人所有的邮箱"""
    file = config.get_config()["raw_data_path"] + f"/{name}_s_all_alias.txt"
    

    if os.path.exists(file):
        with open(file, mode='r', newline='', encoding='utf-8') as file:
            reader = file.readline()
            all_names = ast.literal_eval(reader)
            reader = file.readline()
            all_emails = ast.literal_eval(reader)

            return all_names, all_emails

    url_emails = r'https://api.github.com/users/' + name + r'/events/public'
    json_data = query_api(url_emails)

    all_emails = set()  # 使用 set 来存储邮箱以去重
    all_names = set()   # 使用 set 来存储名字以去重

    all_names.add(name)

    try:
        for item in json_data:
            if item['type'] == 'PushEvent':
                all_names.add(item['actor']['login'])
                all_names.add(item['actor']['display_login'])
            elif item['type'] == 'IssueCommentEvent':
                all_names.add(item['actor']['login'])
                all_names.add(item['actor']['display_login'])
            elif item['type'] == 'IssuesEvent':
                all_names.add(item['actor']['login'])
                all_names.add(item['actor']['display_login'])
            else:
                continue

    except Exception as e:
        raise Exception(e)

    with open(file, mode='w', newline='', encoding='utf-8') as file:
        file.write(str(all_names))
        file.write('\n')
        file.write(str(all_emails))

    return all_names, all_emails

def get_sliced_commits(owner_name, repo_name, slice_rules, name) -> list:
    # 读取 CSV 文件
    csv_file = config.get_config()["raw_data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"

    if not os.path.exists(csv_file):
        name_set, email_set = get_developer_s_all_alias(name)
        get_developer_s_all_commits_on_specific_repo(owner_name, repo_name, name, name_set, email_set)

    df = pd.read_csv(csv_file, na_values=["-", "", "\"-\""])

    df['date'] = df['date'].apply(lambda x: parse_datetime(x))
    
    # 存储每个切片的数量
    counts = []
    
    for start_date, end_date in slice_rules:
        count = df[(df['date'] >= start_date) & (df['date'] < end_date)].shape[0]
        counts.append(count)

    return counts

def get_sliced_commits_on_all_repos(name, slice_rules):
    csv_file = config.get_config()["raw_data_path"] + f"/{name}_s_sliced_commits_on_all_repos.csv"

    if os.path.exists(csv_file):
        try:
            return pd.read_csv(csv_file)
        except Exception as e:
            return pd.DataFrame(["hash", "author_name", 
                                 "author_email", "date", 
                                 "message", "added", "removed", "fname"])

    repos = get_developer_s_all_repos(name)

    # 定义一个字典来存储结果
    results = {}

    # 定义一个函数以便在多线程中使用
    def process_repo(repo):
        counts = get_sliced_commits(repo.split("/")[0], repo.split("/")[1], slice_rules, name)
        results[repo] = counts

    # 使用 ThreadPoolExecutor 进行多线程处理
    with ThreadPoolExecutor(max_workers=config.get_config()["inner_parrallel"]) as executor:
        executor.map(process_repo, repos)

    # 将结果转换为 DataFrame
    df = pd.DataFrame.from_dict(results, orient='index').T

    logger.info(f"Write {len(df)} commits to {csv_file}")

    df.to_csv(csv_file, index=False)

    return df

def calc_developers_focuse_rate_on_repo(name, owner_name, repo_name, slice_rules):

    df = get_sliced_commits_on_all_repos(name, slice_rules)

    # 计算每行指定仓库数据占所有数据的比重
    total_counts = df.sum(axis=1)  # 每行的总和
    try:
        repo_counts = df[f"{owner_name}/{repo_name}"]  # 指定仓库的数据
    except KeyError:
        return [0] * len(slice_rules)

    # 计算比重，避免除以零
    proportions = repo_counts / total_counts.replace(0, 1)  # 将零替换为1以避免除以零
    proportions = proportions.fillna(0)  # 将 NaN 替换为 0

    return proportions.to_list()

def calc_ave_focus_rate(truck_factor, owner_name, repo_name, slice_rules):
    authors = truck_factor["authors"]
    results = []

    def process_author(author):
        author = str(author)
        author = ast.literal_eval(author)
        list_results = []
        
        for i in author:
            counts = calc_developers_focuse_rate_on_repo(i, owner_name, repo_name, slice_rules)
            list_results.append(counts)
        
        df = pd.DataFrame(list_results).T
        return df.mean(axis=1).tolist()

    with ThreadPoolExecutor(max_workers=config.get_config()["inner_parrallel"]) as executor:
        # 使用列表推导式提交任务并收集结果
        results = list(executor.map(process_author, authors))

    df = pd.DataFrame(results)

    return df.mean(axis=0).tolist()
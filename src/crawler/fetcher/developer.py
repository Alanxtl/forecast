import ast
import os
import re
from pathlib import Path
import subprocess
import ast
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
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

def write_git_log_to_file_author(owner_name, repo_name):
    path_to_repo = f"{owner_name}/{repo_name}" + r".git"
    
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

def get_developer_s_all_commits_on_specific_repo(owner_name, repo_name):
    csv_file = conf["raw_data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    if os.path.exists(csv_file):
        return csv_file

    evo_log = write_git_log_to_file_author(owner_name, repo_name)
    evo_log = convert(evo_log, csv_file)
    evo_log = repair(evo_log)
    
    evo_log = simple(evo_log)
    
    logger.info(f"Write {len(evo_log)} commits to {evo_log}")

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

    to_file = config.get_config()["raw_data_path"] + f"/{name}_s_commits_on_{owner_name}_{repo_name}.csv"

    if os.path.exists(to_file):
        return pd.read_csv(to_file).iloc[:, 0].to_list()

    # 读取 CSV 文件
    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    name_set, email_set = get_developer_s_all_alias(name)

    logger.info(f"Getting {name}'s commits on {owner_name}/{repo_name}")

    if not os.path.exists(csv_file):
        get_developer_s_all_commits_on_specific_repo(owner_name, repo_name)

    df = pd.read_csv(csv_file, na_values=["-", "", "\"-\""])

    df['date'] = df['date'].apply(lambda x: parse_datetime(x))
    
    # 存储每个切片的数量
    counts = []
    
    for start_date, end_date in slice_rules:
        filter = df[(df['date'] >= start_date) & 
                   (df['date'] < end_date)]
        
        # 过滤出指定开发者的提交
        filter = filter[(filter["author_email"].apply(lambda x: x.split("@")[0]).isin(email_set)) | 
                       (filter["committer_email"].apply(lambda x: x.split("@")[0]).isin(email_set)) |
                       (filter["author_name"].isin(name_set)) |
                       (filter["committer_name"].isin(name_set))]

        count = filter.shape[0]
        counts.append(count)

    pd.DataFrame(counts).to_csv(to_file, index=False)

    logger.info(f"Write {len(counts)} commits to {to_file}")

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
    with ThreadPoolExecutor(max_workers=config.get_config()["clone_parrallel"]) as executor:
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
    # 获取所有作者列表
    # print(truck_factor)
    authors = truck_factor["authors"]
    
    # 用于保存每个作者的计算结果，避免重复计算
    author_cache = {}
    
    # 提取所有作者并去重
    unique_authors = set()
    for author_list in authors:
        author_list = ast.literal_eval(str(author_list))
        for author in author_list:
            unique_authors.add(author)

    # 定义处理单个作者的函数
    def process_author(author):
        counts = calc_developers_focuse_rate_on_repo(author, owner_name, repo_name, slice_rules)
        author_cache[author] = counts  # 将结果缓存起来
        return counts

    # 使用多线程计算去重后的所有作者的结果
    with ThreadPoolExecutor(max_workers=config.get_config()["inner_parrallel"]) as executor:
        executor.map(process_author, unique_authors)

    # 将结果映射回原始的作者列表
    results = []
    for author_list in authors:
        author_list = ast.literal_eval(str(author_list))
        list_results = [author_cache[author] for author in author_list]
        
        # 计算当前作者列表的平均值
        df = pd.DataFrame(list_results).T
        results.append(df.mean(axis=1).tolist())

    # 将所有结果转换为 DataFrame，并计算最终的平均值
    df = pd.DataFrame(results)
    return df.mean(axis=0).tolist()
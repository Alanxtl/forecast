from concurrent.futures import ThreadPoolExecutor
import os
import threading
import ast

import pandas as pd
from loguru import logger

from src.config import Config as config
from src.utils.graphql import query_api
from src.utils.datetime_parser import parse_datetime

def totalPages(owner_name, repo_name) -> int:
    query_url = f'https://api.github.com/repos/{owner_name}/{repo_name}/issues?per_page=1&page=1'
    response = query_api(query_url)[0]["number"]
    return response / 100

def lastPage(owner_name, repo_name) -> int:
    return int(totalPages(owner_name, repo_name) + 1)

def get_all_issues(owner_name, repo_name) -> pd.DataFrame:
    """获取某库所有的 PR 信息"""
    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_issues.csv"

    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)

    rets = []
    lock = threading.Lock()
    page = 1
    last = lastPage(owner_name, repo_name)  

    def worker(current_page):
        nonlocal rets, page
        query_url = f'https://api.github.com/repos/{owner_name}/{repo_name}/issues?per_page=100&page={current_page}'
        logger.debug(f"{csv_file} cursor at {current_page}")
        try:
            response = query_api(query_url)  # 假设您有这个函数来发送请求
            with lock:
                rets.extend(response)  # 解析时间戳等信息
        except Exception as e:
            with lock:
                page = current_page
            logger.error(f"Error querying page {current_page}: {e}")

    with ThreadPoolExecutor(max_workers=6) as executor:
        while page <= last:
            executor.submit(worker, page)
            page += 1

    # 写入 CSV 文件
    df = pd.DataFrame(rets, columns=["created_at", "updated_at", "closed_at", "user", "labels"])  # 根据需要调整列
    df["user"] = df["user"].apply(lambda x: x["login"])  # 从用户对象中提取登录名
    df["labels"] = df["labels"].apply(lambda x: len(ast.literal_eval(x)))  # 从用户对象中提取登录名
    df.to_csv(csv_file, index=False, encoding='utf-8')

    logger.info(f"Write {len(rets)} PRs to {csv_file}")

    return df

def get_sliced_issues(owner_name, repo_name, slice_rules):
    # 读取 CSV 文件
    df = get_all_issues(owner_name, repo_name)

    # 转换 createdAt 和 closedAt 列
    df['created_at'] = df['created_at'].apply(parse_datetime)
    df['updated_at'] = df['updated_at'].apply(lambda x: None if pd.isna(x) else parse_datetime(x))
    df['closed_at'] = df['closed_at'].apply(lambda x: None if pd.isna(x) else parse_datetime(x))
    df['labels'] = df['labels'].astype(int)
    
    # 存储每个切片的数量
    created_counts = []
    lable_counts = []
    
    for start_date, end_date in slice_rules:
        filter = df[(df['created_at'] >= start_date) & (df['created_at'] < end_date)]
        count = filter.shape[0]
        lable = filter['labels'].sum()
        created_counts.append(count)
        lable_counts.append(int(lable))

    # 存储每个切片的数量
    close_counts = []
    
    for start_date, end_date in slice_rules:
        count = df[(df['closed_at'] >= start_date) & (df['closed_at'] < end_date)].shape[0]
        close_counts.append(count)

    return created_counts, close_counts, lable_counts

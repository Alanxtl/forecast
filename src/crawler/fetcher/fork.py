from concurrent.futures import ThreadPoolExecutor
import os
import threading

import pandas as pd
from loguru import logger

from src.config import Config as config
from src.utils.api import query_api
from src.utils.datetime_parser import parse_datetime
from src.crawler.fetcher.repo import get_repo_s_info

def totalPages(owner_name, repo_name) -> int:
    return get_repo_s_info(owner_name, repo_name)["forks_count"] / 100

def lastPage(owner_name, repo_name) -> int:
    return int(totalPages(owner_name, repo_name) + 1)

def get_repo_s_all_forks(owner_name, repo_name) -> pd.DataFrame:
    """获取某库所有的 fork 信息"""
    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_s_forks.csv"

    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)

    rets = []
    lock = threading.Lock()
    page = 1
    last = lastPage(owner_name, repo_name)

    def worker(current_page):
        nonlocal rets
        for i in range(current_page, min(last, current_page + 10)):
            query_url = f'https://api.github.com/repos/{owner_name}/{repo_name}/forks?per_page=100&page={i}'
            logger.debug(f"{csv_file} cursor at {i}")
            try:
                response = query_api(query_url)
                with lock:
                    rets.extend(response)
            except Exception as e:
                logger.error(f"Error querying page {i}: {e}")

    with ThreadPoolExecutor(max_workers=config.get_config()["api_parrallel"]) as executor:
        while page <= last:
            executor.submit(worker, page)
            page += 10

    # 写入 CSV 文件
    df = pd.DataFrame(rets, columns=["created_at", "updated_at", "pushed_at", "owner"])  # 根据需要调整列
    df["owner"] = df["owner"].apply(lambda x: x["login"])  # 从用户对象中提取登录名

    df.to_csv(csv_file, index=False, encoding='utf-8')

    logger.info(f"Write {len(rets)} forks to {csv_file}")

    return df

def get_sliced_forks(owner_name, repo_name, slice_rules):
    df = get_repo_s_all_forks(owner_name, repo_name)

    df['created_at'] = df['created_at'].apply(lambda x: parse_datetime(x))
    
    counts = []
    
    for start_date, end_date in slice_rules:
        count = df[(df['created_at'] >= start_date) & (df['created_at'] < end_date)].shape[0]
        counts.append(count)

    return counts


from concurrent.futures import ThreadPoolExecutor
import os
import threading

import pandas as pd
from loguru import logger

from src.config import Config as config
from src.utils.api import query_star
from src.utils.datetime_parser import parse_datetime
from src.crawler.fetcher.repo import get_repo_s_info

def totalPages(owner_name, repo_name) -> int:
    return get_repo_s_info(owner_name, repo_name)["stargazers_count"] / 100

def lastPage(owner_name, repo_name) -> int:
    return min(int(totalPages(owner_name, repo_name) + 1), 400)

def get_repo_s_all_stars(owner_name, repo_name) -> pd.DataFrame:
    """获取某库所有的 star 信息"""
    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_s_stars.csv"

    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)

    rets = []
    lock = threading.Lock()
    page = 1
    last = lastPage(owner_name, repo_name)

    def worker(current_page):
        nonlocal rets
        for i in range(current_page, min(last, current_page + 10)):
            query_url = f'https://api.github.com/repos/{owner_name}/{repo_name}/stargazers?per_page=100&page={i}'
            logger.debug(f"{csv_file} cursor at {i}")
            try:
                response = query_star(query_url)
                with lock:
                    rets.extend([parse_datetime(item) for item in response])
            except Exception as e:
                logger.error(f"Error querying page {i}: {e}")

    with ThreadPoolExecutor(max_workers=config.get_config()["api_parrallel"]) as executor:
        while page <= last:
            executor.submit(worker, page)
            page += 10

    # 写入 CSV 文件
    df = pd.DataFrame(rets, columns=["starred_at"])
    df.to_csv(csv_file, index=False, encoding='utf-8')

    logger.info(f"Write {len(rets)} stars to {csv_file}")

    return df

def get_sliced_stars(owner_name, repo_name, slice_rules):
    # 读取 CSV 文件
    df = get_repo_s_all_stars(owner_name, repo_name)

    # 转换 createdAt 和 closedAt 列
    df['starred_at'] = df['starred_at'].apply(lambda x: parse_datetime(x))
    
    # 存储每个切片的数量
    counts = []
    
    for start_date, end_date in slice_rules:
        count = df[(df['starred_at'] >= start_date) & (df['starred_at'] < end_date)].shape[0]
        counts.append(count)

    return counts


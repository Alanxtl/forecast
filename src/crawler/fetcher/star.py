import datetime
import os
from datetime import datetime
import threading

import pandas as pd
from loguru import logger

from src.config import Config as config
from src.utils.graphql import query_star
from src.utils.datetime_parser import parse_datetime
from src.crawler.repo import get_repo_s_info

def totalPages(owner_name, repo_name) -> int:
    return get_repo_s_info(owner_name, repo_name)["stargazers_count"] / 100

def lastPage(owner_name, repo_name) -> int:
    return int(totalPages(owner_name, repo_name) + 1)

def get_repo_s_all_stars(owner_name, repo_name) -> pd.DataFrame:
    """获取某库所有的 star 信息"""
    csv_file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_s_stars.csv"

    if os.path.exists(csv_file):
        with open(csv_file, mode='r', newline='', encoding='utf-8') as csv_file:
            try:
                complete_df = pd.read_csv(csv_file)
            finally:
                csv_file.close()

            return complete_df

    rets = []
    lock = threading.Lock()
    condition = threading.Condition()
    page = 1
    thread_count = 0
    last = lastPage(owner_name, repo_name)

    def worker():
        nonlocal page, rets, thread_count, last

        with condition:
            current_page = page
            page += 10

            if current_page > last:
                thread_count -= 1
                condition.notify_all()
                return

        for i in range(current_page, min(last, current_page + 10)):
            quert_url = 'https://api.github.com/repos/%s/%s/stargazers?per_page=100&page=%d' % (owner_name, repo_name, i)
            try:
                response = query_star(quert_url)
            except Exception as e:
                logger.error(f"Error querying page {i}: {e}")
                continue
            with lock:
                rets.extend([parse_datetime(i) for i in response])
                logger.debug(f"{csv_file} cursor at {i}")

        with condition:
            thread_count -= 1
            condition.notify_all()
            return 
        
    while True:
        t = threading.Thread(target=worker)
        t.start()
        thread_count += 1
        if thread_count >= 6:
            with condition:
                condition.wait()
        if page >= last - 1:
            break

    # 等待所有线程完成
    while thread_count > 0:
        with condition:
            condition.wait()

    # 写入 CSV 文件
    df = pd.DataFrame(rets, columns=["starred_at"])
    df.to_csv(csv_file, index=False, encoding='utf-8')

    logger.info(f"Write {len(rets)} commits to {csv_file}")

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


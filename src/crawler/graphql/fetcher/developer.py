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
from graphql import query_contributions_api
from utils import parse_datetime
from query_templates import developer_s_all_issues

def get_developer_s_all_commits(name):
    csv_file = config.Config.get_config()["data_path"] + f"/{name}_s_all_commits.csv"

    quert_url = 'https://github-contributions-api.jogruber.de/v4/%s' % name
    response = query_contributions_api(quert_url)
    
    rets = []
    for i in response["contributions"]:
        if i['count'] > 0:
            rets.append({'date': i['date'], 
                         'count': i['count']})


    # 写入 CSV 文件
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        try:
            writer = csv.DictWriter(file, fieldnames=["date", "count"])
            writer.writeheader()  # 写入表头
            writer.writerows(rets)  # 写入所有提交信息
        finally:
            file.close()

    logger.info(f"Write {len(rets)} commits to {csv_file}")

def get_commit_count_from_to(name, start: datetime, end: datetime):
    csv_file = config.Config.get_config()["data_path"] + f"/{name}_s_all_commits.csv"

    if not os.path.exists(csv_file):
        get_developer_s_all_commits(name)

    count = 0

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            check = 1
            reader = csv.DictReader(file)
            for row in reader:
                t = time.strptime(row['date'], "%Y-%m-%d")
                if t < end and t >= start:
                    check = 2
                    count += int(row['count'])
                elif check == 2:
                    check == 3
                if check == 3:
                    break
        finally:
            file.close()

    return count


if __name__ == "__main__":
    print(get_commit_count_from_to("Alanxtl", time.strptime("2024-01-01", "%Y-%m-%d"), time.strptime("2025-01-01", "%Y-%m-%d")))

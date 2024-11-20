import ast
import os

from loguru import logger

from src.config import Config as config
from src.utils.api import query_api

def get_repo_s_info(owner_name, repo_name) -> dict: 
    """获取某 repo 的基本信息"""
    file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_s_info.txt"

    if os.path.exists(file):
        with open(file, mode='r', newline='', encoding='utf-8') as file:
            try:
                reader = file.readline()
                json_data = ast.literal_eval(reader)
            finally:
                file.close()

            return json_data

    url_repos = f'https://api.github.com/repos/{owner_name}/{repo_name}'
    json_data = query_api(url_repos)

    with open(file, mode='w', newline='', encoding='utf-8') as f:
        try:
            f.write(str(json_data))
        finally:
            f.close()

    logger.info(f"Get {owner_name}/{repo_name}'s info, write to {file}")

    return json_data
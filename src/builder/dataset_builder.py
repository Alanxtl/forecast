from concurrent.futures import ThreadPoolExecutor
import traceback
from loguru import logger

from src.dataset import repo
from src.config import Config as config

def process_repository(repo_str):
    owner, name = repo_str.split("/")
    r = repo(owner, name)
    try:
        r.to_dataset()
    except Exception as e:
        logger.error(f"Error processing {repo_str}: {traceback.print_exc()} {e}")

def build(str):
    # 读取文件内容
    with open(str, 'r') as file:
        repos = file.read().strip().splitlines()

    # 使用 ThreadPoolExecutor 来并行处理
    with ThreadPoolExecutor(max_workers=config.get_config()["clone_parrallel"]) as executor:
        executor.map(process_repository, repos)

import os
from loguru import logger

from src.dataset import repo
from src.config import Config as config
from src.utils.repair_git_move import repair
from src.utils.graphql import query_star
from src.crawler.fetcher.star import get_sliced_stars, get_repo_s_all_stars
from src.crawler.repo import get_repo_s_info
from src.crawler.fetcher.developer import calc_developers_focuse_rate_on_repo, get_sliced_commits

conf = config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

if not os.path.exists(conf["data_path"]):
    os.mkdir(conf["data_path"])
if not os.path.exists(conf["raw_data_path"]):
    os.mkdir(conf["raw_data_path"])
if not os.path.exists(conf["predict_data_path"]):
    os.mkdir(conf["predict_data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":
    hertzbeat = repo("apache", "hertzbeat")
    hertzbeat.get_commit_data()
    hertzbeat.get_social_data()


# ab3f51d883d0c0909bc92a31e599bea3e69a8c06
import os
from loguru import logger

from src.crawler.fetcher.commits import *
from src.crawler.fetcher.issues import *
from src.crawler.truck_factor.compute import compute
from src.config import Config as config

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
    print("main: ")
    a, rules = slice_all_commit_data("apache", "hertzbeat")

    print(get_sliced_issues("apache", "hertzbeat", rules))


# ab3f51d883d0c0909bc92a31e599bea3e69a8c06
import os
import time
from loguru import logger
from src.crawler.graphql.fetcher.commits import *
import src.config as config

conf = config.Config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

if not os.path.exists(conf["data_path"]):
    os.mkdir(conf["data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":
    print(get_specific_developer_s_all_commit("apache", "hertzbeat", "tomsun28"))

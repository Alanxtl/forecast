import os
from loguru import logger
from src.crawler.graphql.fetcher.commits import *
import src.config as config

conf = config.Config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

if not os.path.exists(conf["raw_data_path"]):
    os.mkdir(conf["raw_data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":
    i = slice_all_commit_data("apache", "hertzbeat")
    for j in i:
        print(j[0]["committedDate"], get_slice_data(j), j[-1]["committedDate"])
    # print(i)
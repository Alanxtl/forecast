import os
from loguru import logger

from src.crawler.fetcher.commits import *
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
    i = slice_all_commit_data("apache", "hertzbeat")
    for j in i:
        print(j[0]["committedDate"], get_slice_data(j), j[-1]["committedDate"])
    # print(i)
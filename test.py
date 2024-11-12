import os
from loguru import logger

from src.crawler.fetcher.commits import *
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
    print(compute("Alanxtl", "QT-mychat", None, "94d1d320932287b8751059a98a970c62a46df473"))


# ab3f51d883d0c0909bc92a31e599bea3e69a8c06
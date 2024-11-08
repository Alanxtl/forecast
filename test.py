import os
import time
from loguru import logger
from src.crawler.graphql.fetcher.developer import *
import src.config as config

conf = config.Config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

if not os.path.exists(conf["raw_data_path"]):
    os.mkdir(conf["raw_data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":
    i = calc_developers_focuse_rate_on_repo("Alanxtl", "forecast", "Alanxtl", "2024-10-01")
    print(i)
import os
from loguru import logger
from src.helper.helper import *
import src.config as config

conf = config.Config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

if not os.path.exists(conf["data_path"]):
    os.mkdir(conf["data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":
    all = slice_all_commit_data("XS-MLVP", "env-xs-ov-00-bpu")
    print(len(all))
    for i in all:
        for j in i:
            print(j["committedDate"])
        print("=====================================")

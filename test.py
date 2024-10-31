import os
from loguru import logger
from src.helper.issues import *
import src.config as config

conf = config.Config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

if not os.path.exists(conf["data_path"]):
    os.mkdir(conf["data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":
    get_all_issues("apache", "hertzbeat")

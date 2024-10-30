import os
from loguru import logger
from src.helper.helper import *
logger.add("./log/{time}.log", level="DEBUG")

if not os.path.exists("data"):
    os.mkdir("data")
if not os.path.exists("log"):
    os.mkdir("log")

if __name__ == "__main__":
    get_last_commit_date("XS-MLVP", "env-xs-ov-00-bpu")

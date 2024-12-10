import os
from loguru import logger
import streamlit as st

from src.dataset import repo
from src.config import Config as config
from src.builder.dataset_builder import build, process_repository

conf = config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="INFO")
config.set_token(st.secrets["token"])

if not os.path.exists(conf["data_path"]):
    os.mkdir(conf["data_path"])
if not os.path.exists(conf["raw_data_path"]):
    os.mkdir(conf["raw_data_path"])
if not os.path.exists(conf["predict_data_path"]):
    os.mkdir(conf["predict_data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])
if not os.path.exists(conf["dataset_path"]):
    os.mkdir(conf["dataset_path"])


import sys
import csv
maxInt = sys.maxsize

while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)
        
if __name__ == "__main__":
    list = ["./data/predict/" + i + ".csv" for i in ["LTCs"]]
    for i in list:
        build(i)

# ab3f51d883d0c0909bc92a31e599bea3e69a8c06
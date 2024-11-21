import os
from loguru import logger
import streamlit as st

from src.dataset import repo
from src.config import Config as config
from src.utils.repair_git_move import repair
from src.utils.api import query_star, query_api, get_rate_limit, query_graphql
from src.crawler.fetcher.star import get_sliced_stars, get_repo_s_all_stars
from src.crawler.fetcher.pr import get_repo_all_prs
from src.crawler.fetcher.repo import get_repo_s_info
from src.crawler.fetcher.developer import calc_developers_focuse_rate_on_repo, get_developer_s_all_commits_on_specific_repo, get_sliced_commits
from src.crawler.fetcher.code import write_code_analysis_to_file

conf = config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")
config.set_token(st.secrets["token"])

if not os.path.exists(conf["data_path"]):
    os.mkdir(conf["data_path"])
if not os.path.exists(conf["raw_data_path"]):
    os.mkdir(conf["raw_data_path"])
if not os.path.exists(conf["predict_data_path"]):
    os.mkdir(conf["predict_data_path"])
if not os.path.exists(conf["log_path"]):
    os.mkdir(conf["log_path"])

if __name__ == "__main__":

    str = """{
    search(query: "is:public stars:>15", type: REPOSITORY, first: 100) {
        repositoryCount
        edges {
        node {
            ... on Repository {
            nameWithOwner
            stargazers {
                totalCount
            }
            }
        }
        }
    }
    }"""

    print(query_graphql(str))

# ab3f51d883d0c0909bc92a31e599bea3e69a8c06
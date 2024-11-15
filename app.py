import threading
import time

import streamlit as st
from streamlit_echarts import st_echarts
from loguru import logger

from src.dataset import repo as Repo
from src.config import Config as config

conf = config.get_config()
logger.add(conf["log_path"] + "/{time}.log", level="DEBUG")

st.title("Repository Data Explorer")
owner_name = st.text_input("Enter the Owner Name:")
repo_name = st.text_input("Enter the Repository Name:")

# 创建列布局
col1, col2 = st.columns([2, 1])  # 比例1:2，col2会更宽

with col2:
    with st.expander("Advanced Configuration", expanded=False):
        # st.subheader("Advanced Configuration")
        window_size = st.number_input("Window Size (Months)", min_value=1, value=conf["window_size"])
        step_size = st.number_input("Step Size (Months)", min_value=1, max_value=window_size, value=min(conf["step_size"], window_size))
        predict_size = st.number_input("Predict Size (Months)", min_value=1, value=conf["predict_size"])

# 创建一个字典来存储数据
data = {
    "basic_data": None,
    "commit_data": None,
    "issue_data": None,
    "code_data": None,
}

def fetch_da1(repo):
    data["basic_data"] = repo.get_repo_basic_data()
def fetch_data_0(repo):
    data["commit_data"] = repo.get_commit_data()
def fetch_data_1(repo):
    data["issue_data"] = repo.get_issue_data()
def fetch_data_2(repo):
    data["code_data"] = repo.get_code_data()
def fetch_data_3(repo):
    data["social_data"] = repo.get_social_data()

if st.button("Fetch Data"):

    config.set_size(window_size, step_size, predict_size)

    if owner_name and repo_name:
        state = 0
        progress_bar = st.progress(state)  # 创建进度条
        status_text = st.empty()  # 用于显示状态文本

        state += 5     
        progress_bar.progress(state)

        # 创建 Repo 实例
        repo = Repo(owner_name, repo_name)

        # 创建线程来并行加载数据
        thread1 = threading.Thread(target=fetch_da1, args=(repo, ))
        thread3 = threading.Thread(target=fetch_data_1, args=(repo, ))
        thread4 = threading.Thread(target=fetch_data_2, args=(repo, ))
        thread5 = threading.Thread(target=fetch_data_3, args=(repo, ))

        status_text.text("Fetching data... Please wait.")

        fetch_data_0(repo)

        slice_starts = [str(rule[0].date()) + "~" + str(rule[1].date()) for rule in repo.slice_rules]
        state += 20
        progress_bar.progress(state)

        # 图表0
        options0 = {
            "title": {"text": "Commit Data"},
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Commits", "Modified File Count on Average"]},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "toolbox": {"feature": {"saveAsImage": {}}},
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": slice_starts,
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Commits (n)",  # 主纵坐标名称
                    "position": "left",
                },
                {
                    "type": "value",
                    "name": "Files (n)",  # 副纵坐标名称
                    "position": "right",
                    "offset": 0,  # 调整位置
                },
            ],
            "series": [
                {
                    "name": "Commits",
                    "type": "line",
                    "data": data["commit_data"][0],
                    "yAxisIndex": 0,  # 使用主纵坐标
                },
                {
                    "name": "Modified File Count on Average",
                    "type": "line",
                    "data": data["commit_data"][1],
                    "yAxisIndex": 1,  # 使用副纵坐标
                }
            ],
        }

        # 绘制线图
        st_echarts(options=options0, height="400px", key="Commit_Data")

        thread1.start()
        thread3.start()
        thread4.start()
        thread5.start()

        lock = threading.Lock()
        fu1 = True
        tu1 = True
        tu2 = True
        tu3 = True

        while fu1 or tu1 or tu2:
            time.sleep(0.1)

            # 图表-1
            if not thread1.is_alive() and fu1:
                state += 10
                progress_bar.progress(state)
                opt1 = {
                    "title": {"text": "Repo Basic Data"},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Commits", "Modified File Count on Average"]},
                    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                    "toolbox": {"feature": {"saveAsImage": {}}},
                    "xAxis": {
                        "type": "category",
                        "boundaryGap": False,
                        "data": slice_starts,
                    },
                    "yAxis": [
                        {
                            "type": "value",
                            "name": "Stars (n)",  # 主纵坐标名称
                            "position": "left",
                        },
                    ],
                    "series": [
                        {
                            "name": "Stars",
                            "type": "line",
                            "data": data["basic_data"],
                            "yAxisIndex": 0,  # 使用主纵坐标
                        },
                    ],
                }

                st_echarts(options=opt1, height="400px", key="Repo_Basic_Data")
                with lock:
                    fu1 = False

            # 图表1
            if not thread3.is_alive() and tu1:
                state += 10
                progress_bar.progress(state)
                options1 = {
                    "title": {"text": "Issue Data"},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Created Issues", "Closed Issues", "Issue Label Counts on Average"]},
                    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                    "toolbox": {"feature": {"saveAsImage": {}}},
                    "xAxis": {
                        "type": "category",
                        "boundaryGap": False,
                        "data": slice_starts,
                    },
                    "yAxis": [
                        {
                            "type": "value",
                            "name": "Issues (n)",  # 主纵坐标名称
                            "position": "left",
                        },
                        {
                            "type": "value",
                            "name": "Labels (n)",  # 副纵坐标名称
                            "position": "right",
                            "offset": 0,  # 调整位置
                        },
                    ],
                    "series": [
                        {
                            "name": "Created Issues",
                            "type": "line",
                            "data": data["issue_data"][0],
                            "yAxisIndex": 0,  # 使用主纵坐标
                        },
                        {
                            "name": "Closed Issues",
                            "type": "line",
                            "data": data["issue_data"][1],
                            "yAxisIndex": 0,  # 使用主纵坐标
                        },
                        {
                            "name": "Issue Label Counts on Average",
                            "type": "line",
                            "data": data["issue_data"][2],
                            "yAxisIndex": 1,  # 使用副纵坐标
                        },
                    ],
                }

                st_echarts(options=options1, height="400px", key="Issue_Data")
                with lock:
                    tu1 = False

            # 表2
            if not thread4.is_alive() and tu2:
                state += 10
                progress_bar.progress(state)
                options2 = {
                    "title": {"text": "Code Data"},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Added Code Line", "Removed Code Line"]},
                    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                    "toolbox": {"feature": {"saveAsImage": {}}},
                    "xAxis": {
                        "type": "category",
                        "boundaryGap": False,
                        "data": slice_starts,
                    },
                    "yAxis": {
                        "type": "value",
                        "name": "Lines (n)",  # 主纵坐标名称
                        "position": "left",
                    },
                    "series": [
                        {
                            "name": "Added Code Line",
                            "type": "line",
                            "data": data["code_data"][0],
                            "yAxisIndex": 0,
                        },
                        {
                            "name": "Removed Code Line",
                            "type": "line",
                            "data": data["code_data"][1],
                            "yAxisIndex": 0,
                        },
                    ],
                }

                # 绘制线图
                st_echarts(options=options2, height="400px", key="Code_Data")
                with lock:
                    tu2 = False

            # 表3
            if not thread5.is_alive() and tu3:
                state += 10
                progress_bar.progress(state)
                options3 = {
                    "title": {"text": "Social Data"},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Truck Factor", "Core Developers' Focus Rate"]},
                    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                    "toolbox": {"feature": {"saveAsImage": {}}},
                    "xAxis": {
                        "type": "category",
                        "boundaryGap": False,
                        "data": slice_starts,
                    },
                    "yAxis": {
                        "type": "value",
                        "name": "Lines (n)",  # 主纵坐标名称
                        "position": "left",
                    },
                    "series": [
                        {
                            "name": "Truck Factor",
                            "type": "line",
                            "data": data["social_data"][0],
                            "yAxisIndex": 0,
                        },
                        {
                            "name": "Core Developers' Focus Rate",
                            "type": "line",
                            "data": data["social_data"][1],
                            "yAxisIndex": 0,
                        },
                    ],
                }

                # 绘制线图
                st_echarts(options=options3, height="400px", key="Social_Data")
                with lock:
                    tu3 = False

        thread1.join()
        thread3.join()
        thread4.join()
        thread5.join()

        progress_bar.empty()  # 清空进度条
        status_text.empty()  # 清空状态文本

        repo.out_put_to_log()

        with st.expander("Repository Summary", expanded=False):
            for key, value in repo.get_summary().items():
                st.write(f"**{key}:** {value}")


    else:
        st.warning("Please enter both Owner Name and Repository Name.")
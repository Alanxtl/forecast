import os
import random
from sys import flags
import threading
import time

import streamlit as st
from streamlit_echarts import st_echarts
from loguru import logger

from src.dataset import repo as Repo
from src.config import Config as config

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
if not os.path.exists(conf["dataset_path"]):
    os.mkdir(conf["dataset_path"])

st.title("Repository Data Explorer")
owner_name = st.text_input("Enter the Owner Name:")
repo_name = st.text_input("Enter the Repository Name:")

# 创建列布局
col1, col2 = st.columns([2, 1])  # 比例1:2，col2会更宽

with col2:
    with st.expander("Advanced Configuration", expanded=False):
        # st.subheader("Advanced Configuration")
        window_size = st.number_input("Window Size (Months)", min_value=0.0, value=conf["window_size"], step=0.5)
        step_size = st.number_input("Step Size (Months)", min_value=0.0, max_value=window_size, value=min(conf["step_size"], window_size), step=0.5)
        predict_size = st.number_input("Predict Size (Months)", min_value=1, value=conf["predict_size"])

# 创建一个字典来存储数据
pics = 6
data = {}
threads = []
flags = [True] * pics

def add_threads(key: str, func):
    threads.append(threading.Thread(target=fetch, args=(key, func)))

def fetch(key: str, func):
    data[key] = func()

def generate_chart_options(title, legend_data, x_data, y_axes, series_data):
    return {
        "title": {"text": title},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": legend_data},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "toolbox": {"feature": {"saveAsImage": {}}},
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": x_data,
        },
        "yAxis": y_axes,
        "series": series_data,
    }

if st.button("Fetch Data"):

    # 创建侧边栏
    sidebar = st.sidebar.title("Progress")

    progress_bars = []
    status_texts = []

    for i in range(pics + 1):
        # 在侧边栏中创建进度条
        status_text = st.sidebar.empty()  # 用于显示状态文本
        status_texts.append(status_text)
        progress_bar = st.sidebar.progress(0)
        progress_bars.append(progress_bar)

    config.set_size(window_size, step_size, predict_size)

    if owner_name and repo_name:

        # 创建 Repo 实例
        repo = Repo(owner_name, repo_name)
        st.subheader(f":blue[{owner_name}/{repo_name}] has developed for :green[{repo.display_develop_time}] days!", divider=True)
        

        # 创建线程来并行加载数据
        add_threads("basic_data", repo.get_repo_basic_data)
        add_threads("issue_data", repo.get_issue_data)
        add_threads("code_data", repo.get_code_data)
        add_threads("social_data", repo.get_social_data)
        add_threads("pr_data", repo.get_pr_data)
        add_threads("code_ana_data", repo.get_code_analysis_data)


        progress_bars[0].progress(30)  # 更新进度条
        status_texts[0].markdown(f"Cloning repo")  # 更新状态文本
        
        fetch("commit_data", repo.get_commit_data)

        slice_starts = [str(rule[0].date()) + "~" + str(rule[1].date()) for rule in repo.slice_rules]

        progress_bars[0].progress(100)
        status_texts[0].markdown(f"Repo clone **:green[Success]**")  # 更新状态文本

        # 图表-1
        options0 = generate_chart_options(
            "Commit Data",
            ["Commits", "Commits From Bots", "Modified File Count on Average"],
            slice_starts,
            [
                {"type": "value", "name": "Commits (n)", "position": "left"},
                {"type": "value", "name": "Files (n)", "position": "right", "offset": 0},
            ],
            [
                {"name": "Commits", "type": "line", "data": data["commit_data"][0], "yAxisIndex": 0},
                {"name": "Commits From Bots", "type": "line", "data": data["commit_data"][2], "yAxisIndex": 0},
                {"name": "Modified File Count on Average", "type": "line", "data": data["commit_data"][1], "yAxisIndex": 1},
            ]
        )

        st_echarts(options=options0, height="400px", key="Commit_Data")

        for thread in threads:
            thread.start()

        lock = threading.Lock()

        t = 0

        while any(flags):
            t += 1
            time.sleep(1)
            # print(flags)

            for j in range(1, pics + 1):
                if flags[j - 1]:
                    progress_bars[j].progress(min(90, t + 10 + random.randint(0, 3)))

            # 图表0
            this = 0
            if flags[this]:
                status_texts[this + 1].markdown(f"Fetching Repo Basic Data")
            if not threads[this].is_alive() and flags[this]:
                progress_bars[this + 1].progress(100)
                time.sleep(0.3)
                status_texts[this + 1].markdown("Fetching Repo Basic Data" + " **:green[Done]**")
                opt0 = generate_chart_options(
                    "Repo Basic Data",
                    ["Stars"],
                    slice_starts,
                    [{"type": "value", "name": "Stars (n)", "position": "left"}],
                    [{"name": "Stars", "type": "line", "data": data["basic_data"], "yAxisIndex": 0}]
                )

                st_echarts(options=opt0, height="400px", key="Repo_Basic_Data")
                with lock:
                    flags[this] = False
                    
            # 图表1
            this = 1
            if flags[this]:
                status_texts[this + 1].markdown(f"Fetching Issue Data")
            if not threads[this].is_alive() and flags[this]:
                progress_bars[this + 1].progress(100)
                time.sleep(0.3)
                status_texts[this + 1].markdown("Fetching Issue Data" + " **:green[Done]**")
                opt1 = generate_chart_options(
                    "Issue Data",
                    ["Created Issues", "Closed Issues", "Reopened Issues", "Issue Label Counts on Average"],
                    slice_starts,
                    [
                        {"type": "value", "name": "Issues (n)", "position": "left"},
                        {"type": "value", "name": "Labels (n)", "position": "right", "offset": 0},
                    ],
                    [
                        {"name": "Created Issues", "type": "line", "data": data["issue_data"][0], "yAxisIndex": 0},
                        {"name": "Closed Issues", "type": "line", "data": data["issue_data"][1], "yAxisIndex": 0},
                        {"name": "Reopened Issues", "type": "line", "data": data["issue_data"][3], "yAxisIndex": 1},
                        {"name": "Issue Label Counts on Average", "type": "line", "data": data["issue_data"][2], "yAxisIndex": 1},
                    ]
                )

                st_echarts(options=opt1, height="400px", key="Issue_Data")
                with lock:
                    flags[this] = False

            # 表2
            this = 2
            if flags[this]:
                status_texts[this + 1].markdown(f"Fetching Code Data")
            if not threads[this].is_alive() and flags[this]:
                progress_bars[this + 1].progress(100)
                time.sleep(0.3)
                status_texts[this + 1].markdown("Fetching Code Data" + " **:green[Done]**")
                opt2 = generate_chart_options(
                    "Code Data",
                    ["Added Code Line", "Removed Code Line"],
                    slice_starts,
                    [{"type": "value", "name": "Lines (n)", "position": "left"}],
                    [
                        {"name": "Added Code Line", "type": "line", "data": data["code_data"][0], "yAxisIndex": 0},
                        {"name": "Removed Code Line", "type": "line", "data": data["code_data"][1], "yAxisIndex": 0},
                    ]
                )

                # 绘制线图
                st_echarts(options=opt2, height="400px", key="Code_Data")
                with lock:
                    flags[this] = False
                    
            # 表3
            this = 3
            if flags[this]:
                status_texts[this + 1].markdown(f"Fetching Social Data")
            if not threads[this].is_alive() and flags[this]:
                progress_bars[this + 1].progress(100)
                time.sleep(0.3)
                status_texts[this + 1].markdown("Fetching Social Data" + " **:green[Done]**")
                opt3 = generate_chart_options(
                    "Social Data",
                    ["Truck Factor", "Core Developers' Focus Rate"],
                    slice_starts,
                    [{"type": "value", "name": "Lines (n)", "position": "left"}],
                    [
                        {"name": "Truck Factor", "type": "line", "data": data["social_data"][0], "yAxisIndex": 0},
                        {"name": "Core Developers' Focus Rate", "type": "line", "data": data["social_data"][1], "yAxisIndex": 0},
                    ]
                )

                # 绘制线图
                st_echarts(options=opt3, height="400px", key="Social_Data")
                with lock:
                    flags[this] = False

            # 表4
            this = 4
            if flags[this]:
                status_texts[this + 1].markdown(f"Fetching PR Data")
            if not threads[this].is_alive() and flags[this]:
                progress_bars[this + 1].progress(100)
                time.sleep(0.3)
                status_texts[this + 1].markdown("Fetching PR Data" + " **:green[Done]**")
                opt4 = generate_chart_options(
                    "PR Data",
                    ["Created PRs", "Closed PRs", "PR Handled Time On Average"],
                    slice_starts,
                    [
                        {"type": "value", "name": "PRs (n)", "position": "left"},
                        {"type": "value", "name": "Hours (n)", "position": "right"},
                    ],
                    [
                        {"name": "Created PRs", "type": "line", "data": data["pr_data"][0], "yAxisIndex": 0},
                        {"name": "Closed PRs", "type": "line", "data": data["pr_data"][1], "yAxisIndex": 0},
                        {"name": "PR Handled Time On Average", "type": "line", "data": data["pr_data"][2], "yAxisIndex": 1},
                    ]
                )

                # 绘制线图
                st_echarts(options=opt4, height="400px", key="pr_data")
                with lock:
                    flags[this] = False
                    
            # 表5
            this = 5
            if flags[this]:
                status_texts[this + 1].markdown(f"Fetching Code Data")
            if not threads[this].is_alive() and flags[this]:
                progress_bars[this + 1].progress(100)
                time.sleep(0.3)
                status_texts[this + 1].markdown("Fetching Code Data" + " **:green[Done]**")
                opt5 = generate_chart_options(
                    "Code Data",
                    ["md_files", "md_lines", "code_files", "code_lines", "code_comments"],
                    slice_starts,
                    [
                        {"type": "value", "name": "Lines (n)", "position": "left"},
                        {"type": "value", "name": "Files (n)", "position": "right"},
                    ],
                    [
                        {"name": "md_files", "type": "line", "data": data["code_ana_data"][0], "yAxisIndex": 1},
                        {"name": "md_lines", "type": "line", "data": data["code_ana_data"][1], "yAxisIndex": 0},
                        {"name": "code_files", "type": "line", "data": data["code_ana_data"][2], "yAxisIndex": 1},
                        {"name": "code_lines", "type": "line", "data": data["code_ana_data"][3], "yAxisIndex": 0},
                        {"name": "code_comments", "type": "line", "data": data["code_ana_data"][4], "yAxisIndex": 0},
                    ]
                )

                opt6 = generate_chart_options(
                    "Fork Data",
                    ["Forks"],
                    slice_starts,
                    [
                        {"type": "value", "name": "Forks (n)", "position": "left"},
                    ],
                    [
                        {"name": "Forks", "type": "line", "data": data["code_ana_data"][5], "yAxisIndex": 0},
                    ]
                )

                opt7 = generate_chart_options(
                    "Release Data",
                    ["Releases", "Download Counts"],
                    slice_starts,
                    [
                        {"type": "value", "name": "Releases (n)", "position": "left"},
                        {"type": "value", "name": "Downloads (n)", "position": "right"},
                    ],
                    [
                        {"name": "Releases", "type": "line", "data": data["code_ana_data"][6], "yAxisIndex": 0},
                        {"name": "Download Counts", "type": "line", "data": data["code_ana_data"][7], "yAxisIndex": 1},
                    ]
                )

                # 绘制线图
                st_echarts(options=opt5, height="400px", key="code_ana_data")
                st_echarts(options=opt6, height="400px", key="fork_data")
                st_echarts(options=opt7, height="400px", key="release_data")
                with lock:
                    flags[this] = False
                    

        for thread in threads:
            thread.join()


        repo.out_put_to_log()

        with st.expander("Repository Summary", expanded=False):
            for key, value in repo.get_summary().items():
                st.write(f"**{key}:** {value}")

    else:
        st.warning("Please enter both Owner Name and Repository Name.")

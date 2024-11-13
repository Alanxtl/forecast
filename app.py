import threading
import time

import streamlit as st
from streamlit_echarts import st_echarts
import pandas as pd
from loguru import logger

from src.dataset import create_repo, repo as Repo

# Streamlit UI
st.title("Repository Data Explorer")

owner_name = st.text_input("Enter the Owner Name:")
repo_name = st.text_input("Enter the Repository Name:")

if st.button("Fetch Data"):
    if owner_name and repo_name:
        progress_bar = st.progress(0)  # 创建进度条
        status_text = st.empty()  # 用于显示状态文本

        # 创建一个线程来执行 Repo 实例创建
        thread = threading.Thread(target=create_repo, args=(owner_name, repo_name, progress_bar.progress))
        thread.start()

        while thread.is_alive():
            status_text.text("Fetching data... Please wait.")
            time.sleep(0.1)  # 每 0.1 秒检查一次线程状态

        # 等待线程结束
        thread.join()

        progress_bar.empty()  # 清空进度条
        status_text.empty()  # 清空状态文本
            
        try:
            repo = Repo(owner_name, repo_name)
            summary = repo.get_summary()

            with st.expander("Repository Summary", expanded=False):
                for key, value in summary.items():
                    st.write(f"**{key}:** {value}")

            # 获得切片规则和数据
            slice_rules = repo.slice_rules
            sliced_commits = repo.sliced_commits

            slice_starts = [str(rule[0].date()) + "~" + str(rule[1].date()) for rule in slice_rules]

            # 图表-1
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
                        "data": repo.added_star_count,
                        "yAxisIndex": 0,  # 使用主纵坐标
                    },
                ],
            }

            # 绘制线图
            st_echarts(options=opt1, height="400px")

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
                        "data": [len(commits) for commits in repo.sliced_commits],
                        "yAxisIndex": 0,  # 使用主纵坐标
                    },
                    {
                        "name": "Modified File Count on Average",
                        "type": "line",
                        "data": repo.modefied_file_count_on_ave,
                        "yAxisIndex": 1,  # 使用副纵坐标
                    }
                ],
            }

            # 绘制线图
            st_echarts(options=options0, height="400px")

            # 图表1
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
                        "data": repo.created_issues,
                        "yAxisIndex": 0,  # 使用主纵坐标
                    },
                    {
                        "name": "Closed Issues",
                        "type": "line",
                        "data": repo.closed_issues,
                        "yAxisIndex": 0,  # 使用主纵坐标
                    },
                    {
                        "name": "Issue Label Counts on Average",
                        "type": "line",
                        "data": repo.lable_counts_on_ave,  # 修正拼写错误
                        "yAxisIndex": 1,  # 使用副纵坐标
                    },
                ],
            }

            # 绘制线图
            st_echarts(options=options1, height="400px")

            # 表2
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
                "yAxis": {"type": "value"},
                "yAxis": [
                    {
                        "type": "value",
                        "name": "Lines (n)",  # 主纵坐标名称
                        "position": "left",
                    },
                ],
                "series": [
                    {
                        "name": "Added Code Line",
                        "type": "line",
                        "data": repo.added_code_line,
                        "yAxisIndex": 0,
                    },
                    {
                        "name": "Removed Code Line",
                        "type": "line",
                        "data": repo.removed_code_line,
                        "yAxisIndex": 0,
                    },
                ],
            }

            # 绘制线图
            st_echarts(options=options2, height="400px")


        except Exception as e:
            st.error(f"Error fetching data: {e}")
    else:
        st.warning("Please enter both Owner Name and Repository Name.")
import json

import streamlit as st

from src.utils.api import get_rate_limit
from src.config import Config as config

conf = config.get_config()
config.set_token(st.secrets["token"])

def check_token(file_path):
    try:        
        # 将输出转换为字典
        data = file_path
        
        # 检查 resources.graphql.remaining 字段
        remaining = data.get('resources', {}).get('graphql', {}).get('remaining')
        core = data.get('resources', {}).get('core', {}).get('remaining')
        # print(data)

        if remaining is None:
            print("--------------Token error, please check your token--------------")
        elif remaining > 1:
            print(f"--------------Token valid, remaining {remaining}, {core}--------------")
        else:
            print(f"--------------Token expire, remaining {remaining}, {core}, please check your token--------------")

    except json.JSONDecodeError:
        print("Failed to parse JSON output")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    check_token(get_rate_limit())
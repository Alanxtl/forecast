import json

from src.utils.graphql import get_rate_limit

def check_token(file_path):
    try:        
        # 将输出转换为字典
        data = file_path
        
        # 检查 resources.graphql.remaining 字段
        remaining = data.get('resources', {}).get('graphql', {}).get('remaining')
        core = data.get('resources', {}).get('core', {}).get('remaining')
        
        if remaining is None:
            print("--------------Token error, please check your token--------------")
        elif remaining > 1:
            print("--------------Token valid, remaining {remaining}, {core}--------------".format(remaining=remaining, core=core))
        else:
            print("--------------Token expire, please check your token--------------")

    except json.JSONDecodeError:
        print("Failed to parse JSON output")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    check_token(get_rate_limit())
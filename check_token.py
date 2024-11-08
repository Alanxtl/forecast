import json
import sys

def check_token(file_path):
    try:
        # 读取 JSON 文件
        with open(file_path, 'r') as f:
            output = f.read()
        
        # 将输出转换为字典
        data = json.loads(output.replace("'", '"'))  # 将单引号转换为双引号
        
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
    if len(sys.argv) != 2:
        print("Usage: python check_token.py <output_file>")
    else:
        check_token(sys.argv[1])
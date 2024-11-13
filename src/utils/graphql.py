import requests

from src.config import Config as config

headers = {"Authorization": config.get_config()["token"], 
           "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}

def query_graphql(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
    
def query_api(url: str):
    request = requests.get(url, headers=headers)
    # print(url)
    if request.status_code == 200 or request.status_code == 304:
        return request.json()
    if request.status_code == 409:
        return []
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, url))
    
query_star_headers = {"Authorization": config.get_config()["token"], 
           "Accept": "application/vnd.github.v3.star+json"}

def query_star(url: str):
    request = requests.get(url, headers=query_star_headers)
    # print(url)
    if request.status_code == 200 or request.status_code == 304:
        return [i["starred_at"] for i in request.json()]
    if request.status_code == 409:
        return []
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, url))
    
def get_html(url):
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'
    
    headers = {'User-Agent': user_agent}
    html = requests.get(url, headers=headers)
    # print("html status code is",html.status_code)
    if html.status_code == 200: # 判断请求是否成功
        # print(html)
        return html.text # 返回网页内容
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(html.status_code, url))

def get_rate_limit():
    """获取 GitHub API 的速率限制信息."""
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    
    if response.status_code == 200:
        rate_limit_info = response.json()
        return rate_limit_info
    elif response.status_code == 401:
        return {"message": "Unauthorized"}
    else:
        raise Exception(f"Failed to fetch rate limit info: {response.status_code} {response.text}")


if __name__ == "__main__":
    rate_limit = get_rate_limit()

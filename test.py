import requests
import json
import src.crawler.graphql as graphql
import src.config as config
from loguru import logger
logger.add("./log/{time}.log", level="DEBUG")

def get_data(url, type: str = "vnd.github+json"):
    headers = {
        'Accept': 'application/' + type,
        'Authorization': config.Config.get_config()["token"],
        'X-GitHub-Api-Version': '2022-11-28',}
    html = requests.get(url, headers=headers) # 发送请求

    if html.status_code != 200:
        print("Error get_data: %s" % html.status_code)
        return None

    if str == "vnd.github+json":
        json_data = json.loads(html.text)
        return json_data
    else:
        return html.text


def get_page(url_repos, per_page: int = 100, page: int = 1):
    url_repos = url_repos + '?per_page={per_page}&page={page}'.format(per_page=per_page, page=page)

    data = get_data(url_repos)

    if data == None:
        print("Error get_page: %s" % "data is None")
        return None

    return data

def get_all_pages_commit(repo_owner, repo_name):
    url_repos = 'https://api.github.com/repos/{owner}/{name}/commits'.format(owner=owner, name=name)
    all_commit = []

    for i in range(1, 1000):
        data = get_page(url_repos, page=i)

        if data == None:
            break
        for j in data:
            # try:
            #     commit_url_repos = url_repos + '/{sha}'.format(sha=j['sha'])
            #     get_data(commit_url_repos, type = 'vnd.github.diff')
            # except:
            #     pass

            if j['author'] == None:
                all_commit.append("None")
                continue
            else:
                all_commit.append(j['author']['login'])

    return all_commit

if __name__ == "__main__":
    # owner = "facebookarchive"
    # name = "three20"

    # all_commit = get_all_pages_commit(owner, name)
    # print(len(all_commit))
    #
    #
    q = """
    {
      viewer {
        login
      }
      rateLimit {
        limit
        cost
        remaining
        resetAt
      }
    }
    """
    print(graphql.query(q))

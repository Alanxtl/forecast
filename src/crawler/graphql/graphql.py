import requests
import sys
import os
from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, f'../'))
import config as config

headers = {"Authorization": config.Config.get_config()["token"]}
head = { 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
    }

def query(query): # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers, verify=False)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
    
def query_contributions_api(url): # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.get(url, headers=head, verify=False)
    # print(url)
    if request.status_code == 200 or request.status_code == 304:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
    
if __name__ == "__main__":
    result = query(query) # Execute the query
    remaining_rate_limit = result["data"]["rateLimit"]["remaining"] # Drill down the dictionary
    print("Remaining rate limit - {}".format(remaining_rate_limit))

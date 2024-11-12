from mimetypes import init
import pandas as pd

from src.crawler.fetcher.commits import preprocess_git_log_data
from src.crawler.fetcher.issues import get_all_issues

class repo:

    def __init__(self, owner_name, repo_name):
        self.owner_name = owner_name
        self.repo_name = repo_name
        self.all_commits = pd.read_csv(preprocess_git_log_data(owner_name, repo_name))
        self.modified

        self.all_issues = pd.read_csv(get_all_issues(owner_name, repo_name))


    def get_data(owner_name, repo_name):
    
        data = {}
    
        data["commits_data"] = pd.read_csv(preprocess_git_log_data(owner_name, repo_name))
        data[""]

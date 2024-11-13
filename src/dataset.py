import pandas as pd
from loguru import logger

from src.crawler.fetcher.commits import preprocess_git_log_data, slice_all_commit_data
from src.crawler.fetcher.issues import get_all_issues, get_sliced_issues
from src.crawler.fetcher.star import get_sliced_stars

class repo:

    def __init__(self, owner_name, repo_name):
        self.owner_name = owner_name
        self.repo_name = repo_name

        self.all_commits: pd.DataFrame
        """所有的commit"""
        self.sliced_commits: list
        """新增的commit数量"""
        self.slice_rules: list
        """时间切片方法"""

        self.all_commits = pd.read_csv(preprocess_git_log_data(owner_name, repo_name))
        self.sliced_commits, self.slice_rules = slice_all_commit_data(owner_name, repo_name)

        self.all_issues: pd.DataFrame
        """所有的issue"""
        self.created_issues: list
        """新增issue数量"""
        self.closed_issues: list
        """Closed issue数量"""
        self.lable_counts_in_total: list
        """issue Labels 种类总和"""
        self.lable_counts_on_ave: list
        """issue Labels 平均种类"""

        self.all_issues = pd.read_csv(get_all_issues(owner_name, repo_name))
        self.created_issues, self.closed_issues, self.lable_counts_in_total = get_sliced_issues(owner_name, repo_name, self.slice_rules)
        self.lable_counts_on_ave = [(self.lable_counts_in_total[j] / self.created_issues[j] 
                                         if not self.created_issues[j] == 0 else 0) 
                                         for j in range(len(self.created_issues))]

        self.added_code_line: list
        """新增的代码行数"""
        self.removed_code_line: list
        """删除的代码行数"""
        self.modefied_file_count_in_total: list
        """修改的模块数量总和"""
        self.modefied_file_count_on_ave: list
        """修改的模块数量平均"""

        self.added_code_line = [sum(int(commit["added"]) if not commit["added"] == '-' else 0 for commit in slice) for slice in self.sliced_commits] 
        self.removed_code_line = [sum(int(commit["removed"]) if not commit["added"] == '-' else 0 for commit in slice) for slice in self.sliced_commits] 
        self.modefied_file_count = [sum(int(commit["file_count"]) if not commit["added"] == '-' else 0 for commit in slice) for slice in self.sliced_commits] 
        self.modefied_file_count_on_ave = [(self.modefied_file_count[j] / len(self.sliced_commits[j])
                                            if not len(self.sliced_commits[j]) == 0 else 0)
                                            for j in range(len(self.sliced_commits))]
        
        self.added_star_count: list
        """新增的 star 数"""

        self.added_star_count = get_sliced_stars(owner_name, repo_name, self.slice_rules)

        for i in str(self).split("\n"):
            logger.info(i)

    def __str__(self) -> str:
        str = "%s/%s\n" % (self.owner_name, self.repo_name)
        str += "all_commits (n): %d" % len(self.all_commits) + "\n"
        str += "slices (n): %d" % len(self.slice_rules) + "\n"
        str += "sliced_commits ([n]): %s" % [len(i) for i in self.sliced_commits] + "\n"
        str += "all_issues (n): %d" % len(self.all_issues) + "\n"
        str += "created_issues ([n]): %s" % self.created_issues + "\n"
        str += "closed_issues ([n]): %s" % self.closed_issues + "\n"
        # str += "lable_counts_in_total (n): %s" % self.lable_counts_in_total + "\n"
        str += "lable_counts_on_ave ([n]): %s" % '[' + ", ".join(f"{num:.2f}" for num in self.lable_counts_on_ave) + ']' + "\n"
        str += "added_code_line ([n]): %s" % self.added_code_line + "\n"
        str += "removed_code_line ([n]): %s" % self.removed_code_line + "\n"
        # str += "modefied_file_count ([n]): %s" % self.modefied_file_count + "\n"
        str += "modefied_file_count_on_ave ([n]): %s" % '[' + ", ".join(f"{num:.2f}" for num in self.modefied_file_count_on_ave) + ']' + "\n"
        str += "added_star_count ([n]): %s" % self.added_star_count + "\n"

        return str

    def get_data(self):
        pass

    def get_summary(self):
        return {
            "Owner/Repo": f"{self.owner_name}/{self.repo_name}",
            "All Commits": len(self.all_commits),
            "Slice Rules": len(self.slice_rules),
            "Sliced Commits": [len(i) for i in self.sliced_commits],
            "All Issues": len(self.all_issues),
            "Created Issues": self.created_issues,
            "Closed Issues": self.closed_issues,
            "Label Counts on Average": [f"{num:.2f}" for num in self.lable_counts_on_ave],
            "Added Code Lines": self.added_code_line,
            "Removed Code Lines": self.removed_code_line,
            "Modified File Count on Average": [f"{num:.2f}" for num in self.modefied_file_count_on_ave],
            "Added Star Count": self.added_star_count
        }
    
def create_repo(owner_name, repo_name, progress_bar) -> repo:
    return repo(owner_name, repo_name)
import ast
import pandas as pd
from loguru import logger

from src.crawler.fetcher.commits import preprocess_git_log_data, slice_all_commit_data
from src.crawler.fetcher.issues import get_all_issues, get_sliced_issues
from src.crawler.fetcher.pr import get_repo_all_prs, get_sliced_prs
from src.crawler.fetcher.star import get_sliced_stars
from src.crawler.fetcher.developer import calc_ave_focus_rate
from src.crawler.truck_factor.compute import compute
from src.config import Config as config

conf = config.get_config()

class repo:

    def __init__(self, owner_name, repo_name):
        self.owner_name = owner_name
        self.repo_name = repo_name

        self.all_commits = None
        """所有的commit"""
        self.sliced_commits: list = []
        """新增的commit数量"""
        self.slice_rules: list = []
        """时间切片方法"""

        self.all_issues = None
        """所有的issue"""
        self.created_issues: list = []
        """新增issue数量"""
        self.closed_issues: list = []
        """Closed issue数量"""
        self.lable_counts_in_total: list = []
        """issue Labels 种类总和"""
        self.lable_counts_on_ave: list = []
        """issue Labels 平均种类"""

        self.all_prs = None
        """所有的 PR"""
        self.created_prs: list = []
        """新增的 PR 数"""
        self.closed_prs: list = []
        """关闭的 PR 数"""
        self.pr_length: list = []
        """PR 的平均处理时长"""

        self.added_code_line: list = []
        """新增的代码行数"""
        self.removed_code_line: list = []
        """删除的代码行数"""
        self.modefied_file_count_in_total: list = []
        """修改的模块数量总和"""
        self.modefied_file_count_on_ave: list = []
        """修改的模块数量平均"""

        self.added_star_count: list = []
        """新增的 star 数"""

        self.truck_factor = None
        """truck factor"""
        self.core_developers_focus_rate: list = []
        """核心开发者的关注度"""

    def get_repo_basic_data(self):
        """表-1的数据: star 数"""
        if self.added_star_count == []:
            self.added_star_count = get_sliced_stars(self.owner_name, self.repo_name, self.slice_rules)

        return self.added_star_count
    
    def get_commit_data(self):
        """表0的数据: commit 数 和 修改的文件数
        这个函数必须第一个执行并且不能并行"""

        if self.all_commits is None:
            self.all_commits = pd.read_csv(preprocess_git_log_data(self.owner_name, self.repo_name))
        if self.sliced_commits == []:
            self.sliced_commits, self.slice_rules = slice_all_commit_data(self.owner_name, self.repo_name, window_size=conf["window_size"], step_length=conf["step_size"])
        if self.modefied_file_count_in_total == []:
            self.modefied_file_count_in_total = [sum(int(commit["file_count"]) if not commit["added"] == '-' else 0 for commit in slice) for slice in self.sliced_commits] 
        if self.modefied_file_count_on_ave == []:
            self.modefied_file_count_on_ave = [(self.modefied_file_count_in_total[j] / len(self.sliced_commits[j])
                                            if not len(self.sliced_commits[j]) == 0 else 0)
                                            for j in range(len(self.sliced_commits))]
            
        return [len(commits) for commits in self.sliced_commits], self.modefied_file_count_on_ave
            
    def get_issue_data(self):
        """表1的数据: 新建的 issue 数、关闭的 issue 数 和 issue label 数"""
        if self.all_issues is None:
            self.all_issues = pd.read_csv(get_all_issues(self.owner_name, self.repo_name))
        if self.created_issues == []:
            self.created_issues, self.closed_issues, self.lable_counts_in_total = get_sliced_issues(self.owner_name, self.repo_name, self.slice_rules)
        if self.lable_counts_on_ave == []:
            self.lable_counts_on_ave = [(self.lable_counts_in_total[j] / self.created_issues[j] 
                                         if not self.created_issues[j] == 0 else 0) 
                                         for j in range(len(self.created_issues))]
            
        return self.created_issues, self.closed_issues, self.lable_counts_on_ave

    def get_pr_data(self):
        """表4的数据: 新建的 PR 数、关闭的 PR 数"""

        if self.all_prs is None:
            self.all_prs = get_repo_all_prs(self.owner_name, self.repo_name)
        if self.created_prs == []:
            self.created_prs, self.closed_prs, self.pr_length = get_sliced_prs(self.owner_name, self.repo_name, self.slice_rules)
        
        return self.created_prs, self.closed_prs, self.pr_length

    def get_code_data(self):
        """表2的数据: 新增的代码行数、删除的代码行数 和 修改的模块数"""

        if self.added_code_line == []:
            self.added_code_line = [sum(int(commit["added"]) if not commit["added"] == '-' else 0 for commit in slice) for slice in self.sliced_commits] 
        if self.removed_code_line == []:
            self.removed_code_line = [sum(int(commit["removed"]) if not commit["added"] == '-' else 0 for commit in slice) for slice in self.sliced_commits] 
        
        return self.added_code_line, self.removed_code_line, self.modefied_file_count_on_ave

    def get_social_data(self):
        """表3的数据: 核心开发者的关注度"""

        if self.truck_factor is None:
            self.truck_factor = compute(self.owner_name, self.repo_name, self.slice_rules)
        if self.core_developers_focus_rate == []:
            self.core_developers_focus_rate = calc_ave_focus_rate(self.truck_factor, self.repo_name, self.slice_rules)
        
        return list(self.truck_factor["truckfactor"].to_dict().values()), self.core_developers_focus_rate

    def __str__(self) -> str:
        try:
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
            str += "truck_factor (n): %s" % list(self.truck_factor["truckfactor"].to_dict().keys()) + "\n"
            str += "core_developers (n): %s" % list(self.truck_factor["authors"].to_dict().values()) + "\n"
            str += "core_developers_focus_rate ([n]): %s" % self.core_developers_focus_rate + "\n"
            # str += "pr_in_total (n): %s" % self.all_prs + "\n"
            str += "created_prs ([n]): %s" % self.created_prs + "\n"
            str += "closed_prs ([n]): %s" % self.closed_prs + "\n"
            str += "pr_length ([n]): %s" % self.pr_length + "\n"
        except Exception:
            raise Exception("Data not initialized, please get them first")

        return str

    def get_summary(self):
        try:
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
                "Added Star Count": self.added_star_count,
                "Truck Factor": list(self.truck_factor["truckfactor"].to_dict().keys()),
                "Core Developers": list(self.truck_factor["authors"].to_dict().values()),
                "Core Developers Focus Rate": [f"{num:.2f}" for num in self.core_developers_focus_rate],
                "Created PRs": self.created_prs,
                "Closed PRs": self.closed_prs,
                "PR Length": [f"{num:.2f}" for num in self.pr_length],

            }
        except Exception as e:
            raise Exception("Data not initialized, please get them first")
    
    def update(self):
        self.get_repo_basic_data()
        self.get_commit_data()
        self.get_issue_data()
        self.get_code_data()
        self.get_social_data()
        self.get_pr_data()

    def out_put_to_log(self):
        logger.info(self.__str__())
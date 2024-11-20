"""
The original file is written by HelgeCPH (https://github.com/HelgeCPH/truckfactor)

This program computes the truck factor (also called bus factor) for a given 
Git repository.

The truck factor specifies "...the number of people on your team that have to 
be hit by a truck (or quit) before the project is in serious trouble..."" 
L. Williams and R. Kessler, Pair Programming Illuminated

Note, do not call it from within a Git repository.

More on the truck factor:
  * https://en.wikipedia.org/wiki/Bus_factor
  * https://legacy.python.org/search/hypermail/python-1994q2/1040.html
"""

import re
from typing import Tuple

from loguru import logger
import pandas as pd

from src.crawler.fetcher.commits import preprocess_git_log_data
from src.utils.datetime_parser import parse_datetime
from src.config import Config as config

conf = config.get_config()
TMP = conf["temp_path"]


def create_file_owner_data(df):
    """Currently, we count up how many lines each author added per file.
    That is, we do not compute churn, where we would also detract the amount of
    lines that are removed.

    The author with knowledge ownership is the one that just added the most to
    file. We do not apply a threshold like one must own above 80% or similar.
    """
    new_rows = []

    for fname in set(df.current.values):
        view = df[df.current == fname]
        sum_series = view.groupby(["author_name"]).added.sum()
        view_df = sum_series.reset_index(name="sum_added")
        total_added = view_df.sum_added.sum()

        if total_added > 0:  # For binaries there are no lines counted
            view_df["owning_percent"] = view_df.sum_added / total_added
            owning_author = view_df.loc[view_df.owning_percent.idxmax()]
            new_rows.append(
                (
                    fname,
                    owning_author.author_name,
                    owning_author.sum_added,
                    total_added,
                    owning_author.owning_percent,
                )
            )
        # All binaries are silently skipped in this report...

    owner_df = pd.DataFrame(
        new_rows,
        columns=["artifact", "main_dev", "added", "total_added", "owner_rate"],
    )

    owner_freq_series = owner_df.groupby(["main_dev"]).artifact.count()
    owner_freq_df = owner_freq_series.reset_index(name="owns_no_artifacts")
    owner_freq_df.sort_values(by="owns_no_artifacts", inplace=True)

    return owner_df, owner_freq_df

def compute_truck_factor(df, freq_df) -> Tuple[int, pd.DataFrame]:
    """Similar to G. Avelino et al.
    [*A novel approach for estimating Truck Factors*](https://ieeexplore.ieee.org/stamp)/stamp.jsp?arnumber=7503718)
    we remove low-contributing authors from the dataset as long as still more
    than half of the files have an owner. The amount of remaining owners is the
    bus-factor of that project.
    """
    no_artifacts = len(df.artifact)
    half_no_artifacts = no_artifacts // 2
    count = 0

    if no_artifacts == 0:
        return 0, freq_df

    for idx, (owner, freq) in enumerate(freq_df.values):
        no_artifacts -= freq
        if no_artifacts < half_no_artifacts:
            break
            # TODO: Here the remaining owners have to be collected to be
        else:
            count += 1

    truckfactor = len(freq_df.main_dev) - count
    return truckfactor, freq_df.iloc[idx:].main_dev

def compute(owner_name, repo_name, slice_rules):
    file = config.get_config()["raw_data_path"] + f"/{owner_name}_{repo_name}_truckfactor.csv"

    # if os.path.exists(file):
        # return pd.read_csv(file)

    evo_log_csv = preprocess_git_log_data(owner_name, repo_name)
    complete_df = pd.read_csv(evo_log_csv)

    list = []

    complete_df["date"] = complete_df["date"].apply(lambda x: parse_datetime(x))

    for start_date, end_date in slice_rules:
        df = complete_df[(complete_df['date'] >= start_date) & (complete_df['date'] < end_date)]

        owner_df, owner_freq_df = create_file_owner_data(df)
        truckfactor, authors = compute_truck_factor(owner_df, owner_freq_df)

        list.append({"truckfactor": truckfactor, "authors": authors.tolist()})

    # 定义检测中文或空格的函数
    def contains_chinese_or_space(s):
        pattern = re.compile(r'[\u4e00-\u9fff\s]')
        return bool(pattern.search(s))

    # 定义处理函数，删除符合条件的元素
    def remove_chinese_or_space(lst):
        return [item for item in lst if not contains_chinese_or_space(item)]

    # 应用处理函数到 DataFrame
    df = pd.DataFrame(list)
    df['authors'] = df['authors'].apply(remove_chinese_or_space)
    
    # df.to_csv(file, index=False)

    logger.info(f"Write {len(df)} commits to {file}")

    return df
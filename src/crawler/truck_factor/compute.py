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

import tempfile

import pandas as pd

from src.utils.git_funcs import clone_to_tmp, is_git_url
from src.crawler.fetcher.commits import preprocess_git_log_data

TMP = tempfile.gettempdir()

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

def compute_truck_factor(df, freq_df):
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

def compute(owner_name, repo_name, end_commit_sha = None, start_commit_sha = None):
    evo_log_csv = preprocess_git_log_data(owner_name, repo_name)
    complete_df = pd.read_csv(evo_log_csv)

    first_occurrence_index = -1
    end_occurrence_index = complete_df.index.max()

    if not start_commit_sha is None:
        first_occurrence_index = complete_df[complete_df['hash'] == start_commit_sha].index.max()
    
        if pd.isna(first_occurrence_index):
            raise ValueError(f"commit_sha {start_commit_sha} not found in the log data.")

            
    if end_commit_sha is not None:
        end_occurrence_index = complete_df[complete_df['hash'] == end_commit_sha].index.max()
         
        if pd.isna(end_occurrence_index):
            raise ValueError(f"commit_sha {end_commit_sha} not found in the log data.")


    # 保留从 start_commit_sha 到 end_commit_sha 的行
    complete_df = complete_df.iloc[first_occurrence_index + 1:end_occurrence_index + 1]

    owner_df, owner_freq_df = create_file_owner_data(complete_df)
    truckfactor, authors = compute_truck_factor(owner_df, owner_freq_df)

    return truckfactor, list(authors.values)

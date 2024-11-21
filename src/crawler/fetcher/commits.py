import os
import csv
import subprocess
from pathlib import Path    
from datetime import timedelta

from loguru import logger
import pandas as pd

from src.config import Config as config
from src.utils.datetime_parser import parse_datetime
from src.utils.evo_log_to_csv import convert
from src.utils.repair_git_move import repair, simple
from src.utils.git_funcs import clone_to_tmp

conf = config.get_config()
TMP = conf["temp_path"]

def write_git_log_to_file(owner_name, repo_name):
    path_to_repo = r"https://github.com/" + f"{owner_name}/{repo_name}" + r".git"
    
    p = Path(clone_to_tmp(path_to_repo))

    outfile = os.path.join(TMP, p.name + "_evo.log")

    cmd = (
        f"git -C {p} log "
        r'--pretty=format:"\"%H\",\"%an\",\"%ae\",\"%cn\",\"%ce\",\"%aI\",\"%f\"" '
        f"--date=short --numstat > {outfile}"
    )

    subprocess.run(cmd, shell=True)

    return outfile
    
def preprocess_git_log_data(owner_name, repo_name):
    csv_file = conf["raw_data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    if os.path.exists(csv_file):
        return csv_file

    evo_log = write_git_log_to_file(owner_name, repo_name)
    evo_log = convert(evo_log, csv_file)
    evo_log = repair(evo_log)

    return evo_log

def get_bot_commits(owner_name, repo_name):
    csv_file = conf["raw_data_path"] + f"/{owner_name}_{repo_name}_commits_from_bots.csv"

    if os.path.exists(csv_file):
        return csv_file
    
    all_commit = preprocess_git_log_data(owner_name, repo_name)
    all_commit = pd.read_csv(all_commit)

    bot_commits = all_commit[all_commit["author_name"].str.contains(r"\[bot\]", case=False, na=False) | 
                             all_commit["author_email"].str.contains(r"\[bot\]", case=False, na=False) | 
                             all_commit["committer_name"].str.contains(r"\[bot\]", case=False, na=False) |
                             all_commit["committer_email"].str.contains(r"\[bot\]", case=False, na=False)]    
    
    bot_commits.to_csv(csv_file, index=False)

    csv_file = simple(csv_file)

    logger.info(f"Write {len(bot_commits)} bot commits to {csv_file}")

    return csv_file

def slice_all_commit_data(owner_name, repo_name, window_size: int = conf["window_size"], step_length: int = conf["step_size"]):
    csv_file = conf["raw_data_path"] + f"/{owner_name}_{repo_name}_commits.csv"

    if not os.path.exists(csv_file):
        preprocess_git_log_data(owner_name, repo_name)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            commits = list(reader)
        finally:
            file.close()

    slices = []
    slice_rules = []
    slice_rules_by_sha = []
    total_commits = len(commits)
    window_days = window_size * 30
    step_days = step_length * 30

    # reverse
    current_ptr = total_commits - 1

    while current_ptr >= 0:
        slice_commits = []
        current_start_date = parse_datetime(commits[current_ptr]["date"])
        current_end_date = current_start_date + timedelta(days = window_days)
        next_date = current_start_date + timedelta(days = step_days)
        next_ptr = current_ptr

        while parse_datetime(commits[current_ptr]["date"]) < current_end_date and current_ptr >= 0:
            if parse_datetime(commits[current_ptr]["date"]) < next_date:
                next_ptr = current_ptr - 1
                # print("next =", next_ptr)

            slice_commits.append(commits[current_ptr])

            current_ptr -= 1

        slices.append(slice_commits)
        slice_rules_by_sha.append([slice_commits[0]['hash'], slice_commits[-1]['hash']])
        slice_rules.append([current_start_date, current_end_date])
        current_ptr = next_ptr

    return slices, slice_rules, slice_rules_by_sha

def slice_bot_commit_data(owner_name, repo_name, slice_rules):
    csv_file = conf["raw_data_path"] + f"/{owner_name}_{repo_name}_commits_from_bots.csv"

    if not os.path.exists(csv_file):
        get_bot_commits(owner_name, repo_name)

    df = pd.read_csv(csv_file)
    df["date"] = df["date"].apply(lambda x: parse_datetime(x))

    slices = []
    
    for start_date, end_date in slice_rules:
        slice_commits = df[(df["date"] >= start_date) & (df["date"] < end_date)]
        slices.append(slice_commits)

    return slices

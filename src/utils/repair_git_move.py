"""
The original file is written by HelgeCPH (https://github.com/HelgeCPH/truckfactor)
"""

import sys

import numpy as np
import pandas as pd
from loguru import logger

from src.utils.datetime_parser import parse_datetime

def _deconstruct_git_move(fname):
    if "=>" in fname:
        if "{" in fname and "}" in fname:
            start, end = fname.split(" => ")
            new_piece, tail = end.split("}")
            head, old_piece = start.split("{")
            old = head + old_piece + tail
            new = head + new_piece + tail

            if "//" in old:
                old = old.replace("//", "/")
            if "//" in new:
                new = new.replace("//", "/")
        else:
            old, new = fname.split(" => ")

        return old, new
    else:
        raise Exception("Does not seem to be a file that was moved.")


mapping_seen = {}


def _saw_it_or_ancestor(new_name):
    if new_name in mapping_seen.keys():
        return True
    for line in mapping_seen.values():
        if new_name in line:
            return True
    return False


def _find_previous(data, el):
    # Finds the previous occurrence of el in data
    for idx, (new_name, old_name) in enumerate(data):
        if el == new_name:
            if idx + 1 < len(data):
                shorter_data = data[idx + 1 :]
            else:
                shorter_data = []
            return shorter_data, old_name
    return [], None


def _get_current_for(new_name):
    if new_name in mapping_seen.keys():
        return new_name
    for line in mapping_seen.values():
        if new_name in line:
            return line[0]
    # Should never happen
    return new_name


def repair(log_csv_name):
    df = pd.read_csv(log_csv_name, parse_dates=["date"], na_values=["-", "", "\"-\""])
    if df.empty:
        return log_csv_name
    df["added"] = df["added"].fillna("0").astype(int)
    df["removed"] = df["removed"].fillna("0").astype(int)
    # df["date"] = df["date"].apply(parse_datetime)

    df["current"] = df.fname

    # Commits can be empty, so filter out the commits that do not affect files:
    df_files = df[pd.notna(df.fname)]

    # Create separate columns with old an new names for git mv actions
    df_moves = df_files[df_files.fname.str.contains(" => ")]

    olds_news_currents = []
    for fname in df.fname.values:
        if type(fname) is float:
            # Then it was an empty commit with the float signaling a nan value
            olds_news_currents.append((np.nan, np.nan, np.nan))
        elif "=>" in fname:
            old, new = _deconstruct_git_move(fname)
            olds_news_currents.append((old, new, np.nan))
        else:
            olds_news_currents.append((np.nan, np.nan, np.nan))

    olds, news, currents = list(zip(*list(olds_news_currents)))
    df["old"] = olds
    df["new"] = news
    df["current"] = currents

    # Find only the non-merge commits. They are those that have an `old` and
    # `new` field set but an empty `current` field.
    query = (pd.notna(df.old)) & (pd.notna(df.new)) & (pd.isna(df.current))
    nan_new = list(df[query].new.values)
    nan_old = list(df[query].old.values)

    new_to_old_zip = list(zip(nan_new, nan_old))

    for idx, new_name in enumerate(nan_new):
        if _saw_it_or_ancestor(new_name):
            # This is expensive ...
            continue
        line = []

        start_el = new_name
        shorter = new_to_old_zip[idx:]
        next_el = start_el
        while shorter and next_el:
            line.append(next_el)
            shorter, next_el = _find_previous(shorter, next_el)

        mapping_seen[line[0]] = line

    # And finally build a list that we can assign back to the DataFrame
    final_currents = []
    for _, row in df.iterrows():
        if pd.notna(row.old) and pd.notna(row.new) and pd.isna(row.current):
            final_currents.append(_get_current_for(row.new))
        elif pd.isna(row.old) and pd.isna(row.new) and pd.isna(row.fname):
            # Merging commits without any files attached
            final_currents.append(np.nan)
        elif (
            pd.isna(row.old)
            and pd.isna(row.new)
            and pd.notna(row.fname)
            and pd.isna(row.current)
        ):
            final_currents.append(_get_current_for(row.fname))
    df.current = final_currents

    df['file_count'] = 0

    # # 在合并之前，确保处理 NaN 值并转换为字符串
    # df['fname'] = df['fname'].fillna('-').astype(str)
    # df['current'] = df['current'].fillna('-').astype(str)
    # df['old'] = df['old'].fillna('-').astype(str)
    # df['new'] = df['new'].fillna('-').astype(str)

    # 进行分组，基于 'hash' 字段
    df = df.groupby('hash').agg({
        'added': 'sum',                 # 将 'added' 字段求和
        'removed': 'sum',               # 将 'removed' 字段求和
        'fname': lambda x: list(x.dropna()),  # 合并 'fname' 字段为列表，去除 NaN
        'current': lambda x: list(x.dropna()), # 合并 'current' 字段为列表，去除 NaN
        'old': lambda x: list(x.dropna()),      # 合并 'old' 字段为列表，去除 NaN
        'new': lambda x: list(x.dropna()),      # 合并 'new' 字段为列表，去除 NaN
        'author_name': 'first',         # 保留第一个 author_name
        'author_email': 'first',        # 保留第一个 author_email
        'committer_name': 'first',        # 保留第一个 author_email
        'committer_email': 'first',        # 保留第一个 author_email
        'date': 'first',                # 保留第一个 date
        'message': 'first',             # 保留第一个 message
        'file_count': 'size'            # 计算每组的行数
    }).reset_index()

    # 根据 date 字段排序
    df = df.sort_values(by='date', ascending=False)

    df.to_csv(log_csv_name, index=False)

    logger.info(f"Repair {log_csv_name}")

    return log_csv_name

def simple(log_csv_name):
    df = pd.read_csv(log_csv_name, na_values=["-", "", "\"-\""])
    df["date"] = df["date"].apply(lambda x: parse_datetime(x))
    if df.empty:
        return log_csv_name
    df["added"] = df["added"].fillna("0").astype(int)
    df["removed"] = df["removed"].fillna("0").astype(int)

    df["current"] = df.fname

    df = df.drop(columns=['message', 'added', 'removed', 'fname', 'current', 'old', 'new', 'file_count', 'message']) 
    
    # 进行分组，基于 'hash' 字段
    df = df.groupby('hash').agg({
        'author_name': 'first',         # 保留第一个 author_name
        'author_email': 'first',        # 保留第一个 author_email
        'committer_name': 'first',        # 保留第一个 author_email
        'committer_email': 'first',        # 保留第一个 author_email
        'date': 'first',                # 保留第一个 date
    }).reset_index()

    # 根据 date 字段排序
    df = df.sort_values(by='date', ascending=False)

    df.to_csv(log_csv_name, index=False)

    logger.info(f"Repair {log_csv_name}")

    return log_csv_name


if __name__ == "__main__":
    repair(sys.argv[1])

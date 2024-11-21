from typing import Tuple
import os
import subprocess
from pathlib import Path
import ast

from loguru import logger
import pandas as pd

from src.config import Config as config
from src.utils.git_funcs import clone_to_tmp

conf = config.get_config()
TMP = conf["temp_path"]

def analysis_code(owner_name, repo_name, end_sha) -> Tuple[dict, dict]:
    path_to_repo = r"https://github.com/" + f"{owner_name}/{repo_name}" + r".git"
    outfile = os.path.join(TMP, f"{owner_name}_{repo_name}_cloc_{end_sha}.csv")

    if not os.path.exists(outfile):

        p = Path(clone_to_tmp(path_to_repo))
        cmd = f"cd {p} && cloc {end_sha} --csv --quiet --out {os.path.abspath(outfile)} && cd -" 
        subprocess.run(cmd, shell=True)
        logger.info(f"cloc {p} to {outfile}")

    df = pd.read_csv(outfile)

    df = df.iloc[:, :-1]

    # 抽取 language 为 Markdown 的行
    markdown_row = df[df['language'] == 'Markdown'].sum(numeric_only=True)

    # 计算其余行对每列的求和
    sum_rows = df[df['language'] != 'Markdown'].sum(numeric_only=True)

    return markdown_row.to_dict(), sum_rows.to_dict()

def read_code_analysis_from_file(file_path: str) -> Tuple[list, list, list, list, list]:
    with open(file_path, 'r') as f:
        md_files = ast.literal_eval(f.readline().strip())
        md_lines = ast.literal_eval(f.readline().strip())
        code_files = ast.literal_eval(f.readline().strip())
        code_lines = ast.literal_eval(f.readline().strip())
        code_comments = ast.literal_eval(f.readline().strip())

    return md_files, md_lines, code_files, code_lines, code_comments
    
def write_code_analysis_to_file(owner_name, repo_name, slice_rules) -> Tuple[list, list, list, list, list]:
    path_to_repo = r"https://github.com/" + f"{owner_name}/{repo_name}" + r".git"
    p = Path(clone_to_tmp(path_to_repo))

    md_files: list = []
    md_lines: list = []
    code_files: list = []
    code_lines: list = []
    code_comments: list = []
    
    for _, end in slice_rules:
        md, code = analysis_code(owner_name, repo_name, end)
        md_files.append(md['files'])
        md_lines.append(md['code'])
        code_files.append(code['files'])
        code_lines.append(code['code'])
        code_comments.append(code['comment'])

    file_path = os.path.join(conf["raw_data_path"], f"{owner_name}_{repo_name}_code_ana.csv")

    # 将结果写入文件
    with open(file_path, 'w') as f:
        f.write(str(md_files) + '\n')
        f.write(str(md_lines) + '\n')
        f.write(str(code_files) + '\n')
        f.write(str(code_lines) + '\n')
        f.write(str(code_comments) + '\n')

    logger.info(f"write code analysis to {file_path}")

    return md_files, md_lines, code_files, code_lines, code_comments

def get_code_analysis(owner_name, repo_name, slice_rules) -> Tuple[list, list, list, list, list]:
    file_path = os.path.join(conf["raw_data_path"], f"{owner_name}_{repo_name}_code_ana.csv")
    
    if os.path.exists(file_path):
        return read_code_analysis_from_file(file_path)
    else:
        return write_code_analysis_to_file(owner_name, repo_name, slice_rules)
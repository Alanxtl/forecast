"""
The original file is written by HelgeCPH (https://github.com/HelgeCPH/truckfactor)
"""

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from loguru import logger

from src.config import Config as config

conf = config.get_config()
TMP = conf["temp_path"]

repos = {}

def is_git_url(potential_url):
    result = urlparse(potential_url)
    is_complete_url = all((result.scheme, result.netloc, result.path))
    is_git = result.path.endswith(".git")
    is_git_user = result.path.startswith("git@")
    if is_complete_url:
        return True
    elif is_git_user and is_git:
        return True
    else:
        return False

def is_git_dir(potential_repo_path):
    if not Path(potential_repo_path).is_dir():
        return False
    cmd = f"git -C {potential_repo_path} rev-parse --is-inside-work-tree"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip() == "true"

def clone_to_tmp(url):
    if url in repos:
        return repos[url]

    path = Path(urlparse(url).path)
    outdir = path.name.removesuffix(path.suffix)

    git_repo_dir = os.path.join(TMP, outdir)

    if os.path.exists(git_repo_dir):
        repos[url] = git_repo_dir
        return git_repo_dir
    
    cmd = f"git clone git@github.com:{url} {git_repo_dir}"
    logger.info(cmd)
    subprocess.run(cmd, shell=True)

    repos[url] = git_repo_dir

    return git_repo_dir
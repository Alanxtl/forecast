"""
The original file is written by HelgeCPH (https://github.com/HelgeCPH/truckfactor)
"""

import os
import subprocess
import uuid
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from loguru import logger

TMP = tempfile.gettempdir()

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
    path = Path(urlparse(url).path)
    outdir = path.name.removesuffix(path.suffix)
    git_repo_dir = os.path.join(TMP, outdir + str(uuid.uuid4()))
    cmd = f"git clone {url} {git_repo_dir} > /dev/null 2>&1"
    logger.info(cmd)
    subprocess.run(cmd, shell=True)

    return git_repo_dir
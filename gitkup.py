#!/usr/bin/env python3

# gitlab server easy backup [ahah you got it :>]
# need token with right on API, READ_REPOSITORY

__author__ = "GB Pullarà"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "BSD-3clause"
__version__ = "0.0.1"
__maintainer__ = "gionniboy"
__email__ = "giovbat@gmail.com"
__status__ = "Development"

import os
import sys
import requests
import json
import argparse
from datetime import datetime
from time import gmtime, strftime

from git import Repo

def makedir(BACKUP_DIR):
    try:
        os.mkdir(BACKUP_DIR)
    except OSError as err:
        print(err)
        print("Directory already exists. Skip ...")

def gitkup(BACKUP_DIR, URL, TOKEN):
    pass

def main():
    parser = argparse.ArgumentParser(
        description='Fast backup private repos from gitlab server [api v4]')
    parser.add_argument("--url", help="GitLab Server")
    parser.add_argument("--token", help="Private Token with read permission")
    parser.add_argument(
        "--dest", default="./repos_backup", help="where repositories will be backup (default ./repos_backup")
    args = parser.parse_args()

    URL = args.url
    TOKEN = args.token
    BACKUP_DIR = "./repos_backup"
    if args.dest:
        BACKUP_DIR = args.dest

    makedir(BACKUP_DIR)
    gitkup(BACKUP_DIR, URL, TOKEN)


if __name__ == '__main__':
    main()

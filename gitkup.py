#!/usr/bin/env python3

# gitlab server easy backup [ahah you got it :>]
# need token with right on API, READ_REPOSITORY

__author__ = "GB Pullarà"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "BSD-3clause"
__version__ = "0.0.2"
__maintainer__ = "gionniboy"
__email__ = "giovbat@gmail.com"
__status__ = "Development"

import os
import sys
import signal
import requests
import json
import argparse
from datetime import datetime
from time import gmtime, strftime
from subprocess import Popen, PIPE

import git
from git import Repo, GitCommandError

# TODO: log shit around


def signal_handler(signal, frame):
    """ trap ctrl-c signal """
    print('You pressed Ctrl+C!')
    quit()


def makedir(BACKUP_DIR):
    """ magic!!! """
    if os.path.isdir(BACKUP_DIR) is False:
        try:
            os.mkdir(BACKUP_DIR)
            print("Backup dir created: {}".format(BACKUP_DIR))
        except PermissionError as err:
            print(err)
            sys.exit('permission error')
        except IOError as err:
            print(err)
            sys.exit('IO error')
    else:
        print("Directory exists: skip creation...")


def gitkup(BACKUP_DIR, URL, TOKEN):
    # Request GitLab API to retrieve projects
    gitlab_url = (
        "https://{}/api/v4/projects?visibility=private&private_token={}".format(URL, TOKEN))
    print("Please wait: this operation may take a while ...")
    r = requests.get(gitlab_url)
    if r.status_code != 200:
        # TODO: better status code handling here
        r.raise_for_status()
        print("Error, please retry")
        sys.exit(0)

    projects = r.json()
    for project in projects:
        url = project["ssh_url_to_repo"]
        localPath = "{}/{}.git".format(BACKUP_DIR, project["path"])
        if not os.path.exists(localPath):
            print("Create backup for {}".format(localPath))
            Repo.clone_from(url, localPath)
        else:
            print("Update backup for {}".format(localPath))
            # TODO: refactor this shit
            dir_command = ['cd', localPath]
            git_command = ['git', 'remote', 'update']
            git_query = Popen(git_command)
            backup_state = Popen(dir_command, cwd=BACKUP_DIR,
                                 stdout=PIPE, stderr=PIPE)
            backup_state.communicate()
            git_query.communicate()

def main():
    """ main """
    # Start timestamp
    print("Backup starts at: {}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # Extract url from arguments
    parser = argparse.ArgumentParser(
        description='Fast backup private repos from gitlab server [api v4 - gitlab9.0+]',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--url", default="gitlab.com",
                        type=str, help="GitLab Server url")
    parser.add_argument("--token", required=True, type=str,
                        help="Private Token with read permission")
    parser.add_argument(
        "--dest", default="./repos_backup", help="where repositories will be backup")
    args = parser.parse_args()

    URL = args.url
    TOKEN = args.token
    BACKUP_DIR = args.dest

    makedir(BACKUP_DIR)
    gitkup(BACKUP_DIR, URL, TOKEN)

    # End timestamp
    print("Backup end at: {}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    sys.exit("finish")
    quit()


if __name__ == '__main__':
    try:
        main()
    except GitCommandError as err:
            del err
            sys.exit("Please configure ssh identity on your ssh-agent and retry")
    except:
        signal.signal(signal.SIGINT, signal_handler)
        print('Press Ctrl+C to exit')
        print("Backup end at: {}".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        signal.pause()

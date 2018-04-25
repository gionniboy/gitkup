#!/usr/bin/env python3

# gitlab server easy backup [ahah you got it :>]
# need token with right on API, READ_REPOSITORY

__author__ = "GB Pullarà"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "BSD-3clause"
__version__ = "0.2.2"
__maintainer__ = "gionniboy"
__email__ = "giovbat@gmail.com"
__status__ = "Development"

import os
import sys
import re
import signal
import argparse
from datetime import datetime

import configparser
import logging

import json
import requests

from time import gmtime, strftime
from subprocess import Popen, PIPE

import smtplib
from email.mime.text import MIMEText
import email.utils

import git
from git import Repo, GitCommandError

# TODO: log shit around


def readConfig(default_conf="config.local.ini"):
    """ setup configuration

    :param default_conf: filename
    :param type: string

    :return MAILSERVER: mail server host
    :return type: string

    :return MAILPORT: mail server port
    :return type: int

    :return MAILACCOUNT: mail account sender
    :return type: string

    :return MAILPASSWORD: mail password
    :return type: string

    :return DESTINATIONMAIL: mail account destination
    :return type: string
    """
    if not os.path.exists(default_conf):
        # LOGGER.error('no local config file founded.')
        sys.exit("Create config.local.ini from config.ini and restart.")
    # load configparser with interpolation to allow dynamic config file
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read(default_conf)
    # LOGGER.info("Config file loaded %s", default_conf)
    MAILSERVER = config['MAIL']['SERVER']
    MAILPORT = config['MAIL']['PORT']
    MAILACCOUNT = config['MAIL']['ACCOUNT']
    validate_email(MAILACCOUNT)
    MAILPASSWORD = config['MAIL']['PASSWORD']
    DESTINATIONMAIL = config['MAIL']['DESTINATION']
    validate_email(DESTINATIONMAIL)
    # LOGGER.debug('MAIL - CONFIGURATION LOADED')

    return (MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL)


def validate_email(email):
    """Check if the argument is a syntax-valid email.

    :param email: email string from config
    :param type: string

    :return: validate or exit
    """
    mail_regex = re.compile(
        r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')
    print(email)
    print(mail_regex)
    if not mail_regex.match(email):
        sys.exit("Invalid domain specified.")


# def signal_handler(signal, frame):
#     """ trap ctrl-c signal """
#     print('You pressed Ctrl+C!')
#     quit()


def makedir(BACKUP_DIR):
    """ magic!!!

    :param BACKUP_DIR: filename
    :param type: string

    :return: create dir or print skip
    """
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
    """ Request GitLab API to retrieve projects list and backup

    :param BACKUP_DIR: filename
    :param type: string

    :param URL: gitlab server domain
    :param type: string

    :param TOKEN: private gitlab token
    :param type: string

    : return: git clone or update private repositories
    """
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


def sendmail(MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL, GITLAB_SERVER):
    """ send notification mail

    :param MAILSERVER: mail server host
    :param type: string

    :param MAILPORT: mail server port
    :param type: int

    :param MAILACCOUNT: mail account sender
    :param type: string

    :param MAILPASSWORD: mail password
    :param type: string

    :param DESTINATIONMAIL: mail account destination
    :param type: string

    :param GITLAB_SERVER: gitlab server url
    :param type: string
    """
    print(MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL, GITLAB_SERVER)

    # create email
    message = MIMEText("gitkup task accomplished on {}".format(GITLAB_SERVER))
    message.set_unixfrom(MAILACCOUNT)
    message['From'] = email.utils.formataddr((MAILACCOUNT, MAILACCOUNT))
    message['To'] = email.utils.formataddr(('Recipient', DESTINATIONMAIL))
    message['Subject'] = "GITKUP task from {}".format(GITLAB_SERVER)

    # TODO: make this shit ssl/tls compatible
    # connect to mailserver
    s = smtplib.SMTP_SSL(host=MAILSERVER, port=MAILPORT)
    #s.set_debuglevel(True)
    s.ehlo()
    # If we can encrypt this session, do it
    # print('(starting TLS)')
    # s.starttls()
    # s.ehlo()  # reidentify ourselves over TLS connection

    if s.has_extn('AUTH'):
        print('(logging in)')
        s.login(MAILACCOUNT, MAILPASSWORD)
    else:
        print('(no AUTH)')
        quit()
    # send the message via the server set up earlier.
    s.sendmail(MAILACCOUNT,
                    [DESTINATIONMAIL],
                    message.as_string())
    print("Mail sent succesfully")
    del(message)
    s.quit()


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

    # unpack config
    MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL = readConfig()

    makedir(BACKUP_DIR)
    #gitkup(BACKUP_DIR, URL, TOKEN)
    sendmail(MAILSERVER, MAILPORT, MAILACCOUNT,
             MAILPASSWORD, DESTINATIONMAIL, GITLAB_SERVER=URL)

    # End timestamp
    print("Backup end at: {}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    quit()


if __name__ == '__main__':
    try:
        main()
    except GitCommandError as err:
            del err
            sys.exit("Please configure ssh identity on your ssh-agent and retry")
    except KeyboardInterrupt:
        print("interrupted, stopping ...")
        sys.exit(42)
    # except:
    #     signal.signal(signal.SIGINT, signal_handler)
    #     print('Press Ctrl+C to exit')
    #     print("Backup end at: {}".format(
    #         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    #     signal.pause()

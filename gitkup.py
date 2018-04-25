#!/usr/bin/env python3

# gitlab server easy backup [ahah you got it :>]
# need token with right on API, READ_REPOSITORY

__author__ = "GB Pullarà"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "BSD-3clause"
__version__ = "0.3.3"
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
import logging.config

import json
import requests

from time import gmtime, strftime
from subprocess import Popen, PIPE

import smtplib
from email.mime.text import MIMEText
import email.utils

import git
from git import Repo, GitCommandError


# istanziate logger
LOGGER = logging.getLogger(__name__)


def setup_logging(filepath="logging.json", log_level=logging.INFO):
    """ setup logging based on json dict

    :param filepath: filename
    :param type: string

    """
    if not os.path.exists(filepath):
        LOGGER.error('no logging config file founded.')
        sys.exit('Create logging.json config file and restart.')

    with open(filepath, 'r') as fileconfig:
            config = json.load(fileconfig)
            logging.config.dictConfig(config)
            LOGGER.info('LOGGING SETUP from JSON %s', filepath)

    LOGGER.debug('LOGGING OK - path %s - level %s', filepath, log_level)


def read_config(default_conf="config.local.ini"):
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
        LOGGER.error('no local config file founded.')
        sys.exit("Create config.local.ini from config.ini and restart.")
    # load configparser with interpolation to allow dynamic config file
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read(default_conf)
    LOGGER.info("Config file loaded %s", default_conf)
    MAILSERVER = config['MAIL']['SERVER']
    validate_domain(MAILSERVER)
    MAILPORT = config['MAIL']['PORT']
    MAILACCOUNT = config['MAIL']['ACCOUNT']
    validate_email(MAILACCOUNT)
    MAILPASSWORD = config['MAIL']['PASSWORD']
    DESTINATIONMAIL = config['MAIL']['DESTINATION']
    validate_email(DESTINATIONMAIL)
    LOGGER.debug('MAIL - CONFIGURATION LOADED')

    return (MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL)


def validate_email(email):
    """Check if the argument is a syntax-valid email.

    :param email: email string from config
    :param type: string

    :return: validate or exit
    """
    mail_regex = re.compile(
        r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')
    if not mail_regex.match(email):
        LOGGER.error("Email not valid %s", email)
        sys.exit("Invalid email specified.")


def validate_domain(domain):
    """Check if the argument is a syntax-valid domain.

    :param domain: domain string from positional arg
    :param type: string

    :return: validate or exit
    """
    domain_regex = re.compile(
        r'^(?=.{4,255}$)([a-zA-Z0-9][a-zA-Z0-9-]{,61}[a-zA-Z0-9]\.)+[a-zA-Z0-9]{2,5}$')
    if not domain_regex.match(domain):
        LOGGER.error("Domain not valid %s", domain)
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



    if not os.path.exists(BACKUP_DIR):
        try:
            os.mkdir(BACKUP_DIR)
            LOGGER.info('Backup dir created: %s', BACKUP_DIR)
        except PermissionError as err:
            LOGGER.error(err)
            sys.exit('permission error')
        except IOError as err:
            LOGGER.error(err)
            sys.exit('IO error')
    elif os.path.isfile(BACKUP_DIR):
        LOGGER.error('File exists: %s', BACKUP_DIR)
        sys.exit("file exists - dir can't be create")
    else:
        LOGGER.info("Directory exists: skip creation...")


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
    LOGGER.info("Please wait: this operation may take a while ...")
    r = requests.get(gitlab_url)
    if r.status_code != 200:
        # TODO: better status code handling here
        r.raise_for_status()
        LOGGER.error("Error, please retry")
        sys.exit(0)

    projects = r.json()
    for project in projects:
        url = project["ssh_url_to_repo"]
        localPath = "{}/{}.git".format(BACKUP_DIR, project["path"])
        if not os.path.exists(localPath):
            LOGGER.info("Create backup for %s", localPath)
            Repo.clone_from(url, localPath)
            LOGGER.info("%s cloned", url)
        else:
            LOGGER.info("Update backup for %s", localPath)
            # TODO: refactor this shit
            dir_command = ['cd', localPath]
            git_command = ['git', 'remote', 'update']
            git_query = Popen(git_command)
            backup_state = Popen(dir_command, cwd=BACKUP_DIR,
                                 stdout=PIPE, stderr=PIPE)
            backup_state.communicate()
            git_query.communicate()
            LOGGER.info("%s updated", url)


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
        LOGGER.debug('(logging in)')
        s.login(MAILACCOUNT, MAILPASSWORD)
    else:
        LOGGER.debug('(no AUTH)')
        quit()
    # send the message via the server set up earlier.
    s.sendmail(MAILACCOUNT,
                    [DESTINATIONMAIL],
                    message.as_string())
    LOGGER.info("Mail sent succesfully")
    del(message)
    s.quit()


def main():
    """ main """
    # Start timestamp
    LOGGER.info("Backup starts at: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL = read_config()

    makedir(BACKUP_DIR)
    gitkup(BACKUP_DIR, URL, TOKEN)
    sendmail(MAILSERVER, MAILPORT, MAILACCOUNT,
             MAILPASSWORD, DESTINATIONMAIL, GITLAB_SERVER=URL)

    # End timestamp
    LOGGER.info("Backup end at: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == '__main__':
    try:
        # initializate logging
        setup_logging()
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

#!/usr/bin/env python3

# gitlab server easy backup [ahah you got it :>]
# need token with right on API, READ_REPOSITORY

__author__ = "GB Pullarà"
__copyright__ = "Copyright 2018"
__credits__ = [""]
__license__ = "BSD-3clause"
__version__ = "0.3.4"
__maintainer__ = "gionniboy"
__email__ = "giovbat@gmail.com"
__status__ = "Development"

import os
import sys
import re
# import signal
import argparse
from datetime import datetime

import configparser
import logging
import logging.config

import json

from subprocess import Popen, PIPE

import smtplib
from email.mime.text import MIMEText
import email.utils

import validators
import requests
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
    return True


def read_config(default_conf="config.local.ini", mail=False):
    """ setup configuration

    :param default_conf: filename
    :param type: string

    :param mail: arg flag to mail notification
    :param type: boolean

    :return GITLABSERVER: gitlab server host
    :return type: string

    :return GITLABTOKEN: gitlab private token
    :return type: string

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

    # load gitlab section
    GITLABSERVER = config['GITLAB']['SERVER']
    GITLABTOKEN = config['GITLAB']['TOKEN']

    # load mail section
    if mail == True:
        MAILSERVER = config['MAIL']['SERVER']
        validators.domain(MAILSERVER)
        MAILPORT = config['MAIL']['PORT']
        MAILACCOUNT = config['MAIL']['ACCOUNT']
        validators.email(MAILACCOUNT)
        MAILPASSWORD = config['MAIL']['PASSWORD']
        DESTINATIONMAIL = config['MAIL']['DESTINATION']
        validators.email(DESTINATIONMAIL)
        LOGGER.debug('MAIL - CONFIGURATION LOADED')

        return (GITLABSERVER, GITLABTOKEN, MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL)
    else:
        return (GITLABSERVER, GITLABTOKEN)


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
        "https://{}/api/v4/projects?visibility=private&private_token={}".format(
            URL, TOKEN))
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


def sendmail(MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL, GITLABSERVER):
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

    :param GITLABSERVER: gitlab server url
    :param type: string
    """
    # create email
    message = MIMEText("gitkup task accomplished on {}".format(GITLABSERVER))
    message.set_unixfrom(MAILACCOUNT)
    message['From'] = email.utils.formataddr((MAILACCOUNT, MAILACCOUNT))
    message['To'] = email.utils.formataddr(('Recipient', DESTINATIONMAIL))
    message['Subject'] = "GITKUP task from {}".format(GITLABSERVER)

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


def str2bool(v):
    """
    true/false for argparse mail flag
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse

    :param v:

    :return: true/false or raise exception
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main():
    """ main """
    # Start timestamp
    LOGGER.info("Backup starts at: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # Extract url from arguments
    parser = argparse.ArgumentParser(
        description='Fast backup private repos from gitlab server [api v4 - gitlab9.0+]. Configure before use.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--dest", default="./repos_backup", help="where repositories will be backup")
    parser.add_argument("--mail", type=str2bool, nargs='?', const=True, default=False,
                         help="Activate mail notification.")
    args = parser.parse_args()

    BACKUP_DIR = args.dest

    # unpack config

    if args.mail is True:
        GITLABSERVER, GITLABTOKEN, MAILSERVER, MAILPORT, MAILACCOUNT, MAILPASSWORD, DESTINATIONMAIL = read_config(mail=True)
    else:
        GITLABSERVER, GITLABTOKEN = read_config()

    makedir(BACKUP_DIR)
    gitkup(BACKUP_DIR, GITLABSERVER, GITLABTOKEN)

    if args.mail:
        sendmail(MAILSERVER, MAILPORT, MAILACCOUNT,
                 MAILPASSWORD, DESTINATIONMAIL, GITLABSERVER)

    # End timestamp
    LOGGER.info("Backup end at: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == '__main__':
    try:
        # initializate logging
        setup_logging()
        main()
    except GitCommandError as err:
        LOGGER.error('Git Command Error %s', err)
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

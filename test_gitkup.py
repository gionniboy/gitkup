#!/usr/bin/env python

import os
import pytest
import gitkup


def test_setup_logging():
    """ test logging.json configuration """
    assert gitkup.setup_logging() is True


def test_setup_logging_missing():
    """ test missing logging.json configuration """
    with pytest.raises(SystemExit) as err:
        gitkup.setup_logging(filepath="logging.test")
    assert 'Create logging.json config file and restart.' in str(err.value)


def test_validate_domain():
    """ test domain validation ok"""
    domain = 'python.org'
    assert gitkup.validate_domain(domain) is True


def test_validate_domain_exit():
    """ test domain validation exit """
    domain = 'python.org@it'
    with pytest.raises(SystemExit) as err:
        gitkup.validate_domain(domain)
    assert 'Invalid domain specified.' in str(err.value)


def test_validate_email():
    """ test domain validation ok"""
    email = 'test@python.org'
    assert gitkup.validate_email(email) is True


def test_validate_mail_exit():
    """ test domain validation exit """
    email = 'python.org@it'
    with pytest.raises(SystemExit) as err:
        gitkup.validate_email(email)
    assert 'Invalid email specified.' in str(err.value)

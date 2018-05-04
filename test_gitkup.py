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

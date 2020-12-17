# :coding: utf-8

import os
import getpass
import logging
import tempfile

import pytest
from six.moves import reload_module

import wiz.logging


@pytest.fixture(autouse=True)
def mock_getuser(mocker):
    """Mock getpass.getuser function."""
    mocker.patch.object(getpass, "getuser", return_value="__USER__")


@pytest.fixture()
def mocked_gettempdir(mocker):
    """Return mocked tempfile.gettempdir function."""
    return mocker.patch.object(tempfile, "gettempdir")


@pytest.fixture()
def mocked_config_fetch(mocker):
    """Return mocked wiz.config.fetch function."""
    return mocker.patch.object(wiz.config, "fetch")


@pytest.fixture()
def mocked_dict_config(mocker):
    """Return mocked logging.config.dictConfig function."""
    return mocker.patch.object(logging.config, "dictConfig")


@pytest.mark.parametrize("options, level", [
    ({}, logging.INFO),
    ({"console_level": "info"}, logging.INFO),
    ({"console_level": "debug"}, logging.DEBUG),
    ({"console_level": "warning"}, logging.WARNING),
    ({"console_level": "error"}, logging.ERROR),
], ids=[
    "simple",
    "info",
    "debug",
    "warning",
    "error",
])
def test_initiate(
    temporary_directory, mocked_gettempdir, mocked_config_fetch,
    mocked_dict_config, options, level
):
    """Initiate logger configuration."""
    mocked_gettempdir.return_value = temporary_directory
    mocked_config_fetch.return_value = {}
    reload_module(wiz.logging)

    assert not os.path.isdir(wiz.logging.PATH)

    wiz.logging.initiate(**options)

    assert os.path.isdir(wiz.logging.PATH)
    assert oct(os.stat(wiz.logging.PATH).st_mode) == oct(0o40777)

    mocked_dict_config.assert_called_once_with({
        "version": 1,
        "root": {
            "handlers": ["console", "file"],
            "level": logging.DEBUG
        },
        "formatters": {
            "standard": {
                "class": "coloredlogs.ColoredFormatter",
                "format": "%(message)s"
            },
            "detailed": {
                "class": "logging.Formatter",
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
                "level": level
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "level": logging.INFO,
                "filename": os.path.join(
                    temporary_directory, "wiz", "logs", "__USER__.log"
                ),
                "maxBytes": 10485760,
                "backupCount": 20,
            }
        }
    })


def test_initiate_with_config(
    temporary_directory, mocked_gettempdir, mocked_config_fetch,
    mocked_dict_config
):
    """Initiate logger configuration with custom config."""
    mocked_gettempdir.return_value = temporary_directory
    mocked_config_fetch.return_value = {
        "logging": {
            "root": {
                "handlers": ["console"]
            },
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(message)s"
                }
            }
        }
    }
    reload_module(wiz.logging)

    assert not os.path.isdir(wiz.logging.PATH)

    wiz.logging.initiate()

    assert os.path.isdir(wiz.logging.PATH)
    assert oct(os.stat(wiz.logging.PATH).st_mode) == oct(0o40777)

    mocked_dict_config.assert_called_once_with({
        "version": 1,
        "root": {
            "handlers": ["console"],
            "level": logging.DEBUG
        },
        "formatters": {
            "standard": {
                "class": "coloredlogs.ColoredFormatter",
                "format": "%(asctime)s - %(message)s"
            },
            "detailed": {
                "class": "logging.Formatter",
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
                "level": logging.INFO
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "level": logging.INFO,
                "filename": os.path.join(
                    temporary_directory, "wiz", "logs", "__USER__.log"
                ),
                "maxBytes": 10485760,
                "backupCount": 20,
            }
        }
    })


def test_initiate_with_existing_folder(
    temporary_directory, mocked_gettempdir, mocked_config_fetch
):
    """Initiate logger configuration with existing folder."""
    path = os.path.join(temporary_directory, "wiz", "logs")
    os.makedirs(path, mode=0o755)

    mocked_gettempdir.return_value = temporary_directory
    mocked_config_fetch.return_value = {}
    reload_module(wiz.logging)

    assert os.path.isdir(wiz.logging.PATH)
    assert oct(os.stat(wiz.logging.PATH).st_mode) == oct(0o40755)

    wiz.logging.initiate()

    assert os.path.isdir(wiz.logging.PATH)
    assert oct(os.stat(wiz.logging.PATH).st_mode) == oct(0o40777)

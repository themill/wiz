# :coding: utf-8

from __future__ import absolute_import
import collections
import copy
import getpass
import logging
import logging.config
import os
import tempfile

import coloredlogs

import wiz.config
import wiz.utility
import wiz.filesystem


# Configure custom colors for messages displayed in the console.
coloredlogs.DEFAULT_LEVEL_STYLES = {
    "info": {"color": "cyan"},
    "error": {"color": "red"},
    "critical": {"color": "red"},
    "warning": {"color": "yellow"}
}

#: Available levels with corresponding labels.
LEVEL_MAPPING = collections.OrderedDict([
    ("debug", logging.DEBUG),
    ("info", logging.INFO),
    ("warning", logging.WARNING),
    ("error", logging.ERROR),
])

#: Output path for files exported by default 'file' handler.
PATH = os.path.join(tempfile.gettempdir(), "wiz", "logs")

#: Default configuration for logger.
DEFAULT_CONFIG = {
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
            "level": logging.INFO
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "level": logging.INFO,
            "filename": os.path.join(PATH, "{}.log".format(getpass.getuser())),
            "maxBytes": 10485760,
            "backupCount": 20,
        }
    }
}


def initiate(console_level="info"):
    """Initiate logger configuration.

    :param console_level: Initialize the logging level for the console handler
        if possible. Default is "info".

    .. seealso:: :ref:`configuration/logging`

    """
    config = wiz.config.fetch()

    # Ensure that umask is set to 0 to create log folder with opened
    # permissions for group and other.
    _umask = os.umask(0)

    # Ensure that default output path exists.
    wiz.filesystem.ensure_directory(PATH)

    # Restore previous umask.
    os.umask(_umask)

    # Update default logging configuration if necessary.
    logging_config = copy.deepcopy(DEFAULT_CONFIG)
    wiz.utility.deep_update(logging_config, config.get("logging", {}))

    # Initiate the default level for the console if applicable.
    console_handler = logging_config.get("handlers", {}).get("console")
    if console_handler is not None:
        console_handler["level"] = LEVEL_MAPPING[console_level]

    logging.config.dictConfig(logging_config)


def capture_logs(error_stream, warning_stream):
    """Initialize logger to capture error and warning level.

    :param error_stream: instances of :class:`io.StringIO` which will receive
        all errors logged.

    :param warning_stream: instances of :class:`io.StringIO` which will receive
        all warnings logged.

    """
    logging.config.dictConfig({
        "version": 1,
        "root": {
            "handlers": ["error", "warning"],
            "level": logging.WARNING
        },
        "formatters": {
            "standard": {
                "class": "logging.Formatter",
                "format": "%(message)s"
            },
        },
        "handlers": {
            "error": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": error_stream,
                "level": logging.ERROR,
            },
            "warning": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": warning_stream,
                "level": logging.WARNING,
                "filters": ["warning-filter"]
            }
        },
        "filters": {
            "warning-filter": {
                "()": _WarningLevelFilter,
            }
        },

    })


class _WarningLevelFilter(logging.Filter):
    """Filter out log record with level other than 'WARNING'."""

    def filter(self, record):
        """Return whether *record* is a warning."""
        return record.levelno == logging.WARNING

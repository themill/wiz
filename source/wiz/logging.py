# :coding: utf-8

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

#: Default output path for files exported by
# :class:`~logging.handlers.RotatingFileHandler`.
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

    # Update default logging configuration if necessary.
    logging_config = copy.deepcopy(DEFAULT_CONFIG)
    wiz.utility.deep_update(logging_config, config.get("logging", {}))

    print(logging_config)
    # Initiate the default level for the console if applicable.
    console_handler = logging_config.get("handlers", {}).get("console")
    if console_handler is not None:
        console_handler["level"] = LEVEL_MAPPING[console_level]

    logging.config.dictConfig(logging_config)

# :coding: utf-8

import os
import sys
import time
import getpass
import datetime
import tempfile

import colorama
import pystache
import sawmill
import sawmill.logger.classic
import sawmill.formatter.mustache
import sawmill.handler.stream
import sawmill.formatter.field
import sawmill.filterer.level
import sawmill.filterer.item
import sawmill.compatibility

import wiz.filesystem


#: Top level handler responsible for relaying all logs to other handlers.
root = sawmill.root

#: Log levels ordered by severity. Do not rely on the index of the level name
# as it may change depending on the configuration.
levels = sawmill.levels


def configure(stderr_level="info"):
    """Configure logging handlers.

    A standard error handler is created to output any message with a level
    greater than *stderr_level*.

    A file handler is created to log warnings and greater to :file:`wiz/logs`
    under system temporary directory.

    .. note::

        Standard Python logging are redirected to :mod:`sawmill` to unify
        the logging systems.

    """
    stderr_handler = sawmill.handler.stream.Stream(sys.stderr)
    stderr_formatter = Terminal(
        "{{level}}: {{message}}{{#traceback}}\n{{.}}:{{/traceback}}\n"
    )
    stderr_handler.formatter = stderr_formatter

    stderr_filterer = sawmill.filterer.level.Level(min=stderr_level, max=None)
    stderr_handler.filterer = stderr_filterer

    sawmill.root.handlers["stderr"] = stderr_handler

    logging_path_prefix = os.path.join(tempfile.gettempdir(), "wiz", "logs")
    wiz.filesystem.ensure_directory(logging_path_prefix)

    pid = os.getpid()
    filepath = os.path.join(
        logging_path_prefix, "{}_{}.log".format(pid, int(time.time()))
    )
    file_filterer = sawmill.filterer.level.Level(min="warning", max=None)
    file_stream = open(filepath, "a", 1)
    file_handler = sawmill.handler.stream.Stream(file_stream)
    file_handler.filterer = file_filterer

    file_formatter = sawmill.formatter.field.Field([
        "date", "*", "name", "level", "message", "traceback"
    ])
    file_handler.formatter = file_formatter

    sawmill.root.handlers["file"] = file_handler

    # Configure standard Python logging to redirect all logs to sawmill for
    # handling here. This unifies the logging systems.
    sawmill.compatibility.redirect_standard_library_logging()


class Terminal(sawmill.formatter.mustache.Mustache):
    """:term:`Mustache` template to format :class:`logs <sawmill.log.Log>`.
    """
    _COLOR = {
        "error": colorama.Fore.RED,
        "err": colorama.Fore.RED,
        "warning": colorama.Fore.YELLOW,
        "warn": colorama.Fore.YELLOW,
        "info": colorama.Fore.CYAN,
        "except": colorama.Style.BRIGHT + colorama.Fore.RED,
    }

    def __init__(self, template):
        """Initialize with :term:`Mustache` template."""
        self._renderer = pystache.Renderer(escape=lambda value: value)
        super(Terminal, self).__init__(template, batch=False)

    def format(self, logs):
        """Format *logs* for display."""
        data = []

        for log in logs:
            line = self._renderer.render(self.template, log)

            if "level" in log.keys():
                if log["level"] in self._COLOR.keys():
                    line = (
                        self._COLOR[log["level"]] + line +
                        colorama.Style.RESET_ALL
                    )

            data.append(line)

        return data


class Logger(sawmill.logger.classic.Classic):
    """Extended logger with timestamp and username information."""

    def prepare(self, *args, **kw):
        """Prepare and return a log for emission."""
        log = super(Logger, self).prepare(*args, **kw)

        if "username" not in log:
            log["username"] = getpass.getuser()

        if "date" not in log:
            log["date"] = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

        return log

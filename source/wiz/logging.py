# :coding: utf-8

from __future__ import print_function
import os
import io
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

#: Color symbols.
_COLOR = {
    "error": colorama.Fore.RED,
    "err": colorama.Fore.RED,
    "warning": colorama.Fore.YELLOW,
    "warn": colorama.Fore.YELLOW,
    "info": colorama.Fore.CYAN,
    "except": colorama.Style.BRIGHT + colorama.Fore.RED,
}


def display_info(message):
    """Display an info that will not be handled by :class:`Logger`."""
    print(_COLOR["info"] + message + colorama.Style.RESET_ALL)


def display_error(message):
    """Display an error that will not be handled by :class:`Logger`."""
    print(_COLOR["error"] + message + colorama.Style.RESET_ALL)


def display_green(message):
    """Display a green message that will not be handled by :class:`Logger`."""
    print(colorama.Fore.GREEN + message + colorama.Style.RESET_ALL)


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
    # Stderr handler
    stderr_handler = sawmill.handler.stream.Stream(sys.stderr)
    stderr_formatter = Formatter(
        "{{level}}: {{message}}{{#traceback}}\n{{.}}:{{/traceback}}\n"
    )
    stderr_handler.formatter = stderr_formatter

    stderr_filterer = sawmill.filterer.level.Level(min=stderr_level, max=None)
    stderr_handler.filterer = stderr_filterer

    # File handler
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

    sawmill.root.handlers = {
        "stderr": stderr_handler,
        "file": file_handler
    }

    # Configure standard Python logging to redirect all logs to sawmill for
    # handling here. This unifies the logging systems.
    sawmill.compatibility.redirect_standard_library_logging()


def configure_for_debug():
    """Configure single error handler for debugging purpose.

    A standard error handler is created to log errors and greater into to a
    :class:`io.StringIO` instance.

    A standard waring handler is created to log warnings into to a
    :class:`io.StringIO` instance.

    A tuple with the two :class:`io.StringIO` instances created is returned.

    """
    error_captured = io.StringIO()

    # Error handler
    error_handler = sawmill.handler.stream.Stream(error_captured)
    error_formatter = Formatter(
        "{{level}}: {{message}}{{#traceback}}\n{{.}}:{{/traceback}}\n"
    )
    error_handler.formatter = error_formatter

    error_filterer = sawmill.filterer.level.Level(min="error", max=None)
    error_handler.filterer = error_filterer

    warning_captured = io.StringIO()

    # Warning handler
    warning_handler = sawmill.handler.stream.Stream(warning_captured)
    warning_formatter = Formatter("{{level}}: {{message}}\n")
    warning_handler.formatter = warning_formatter

    warning_filterer = sawmill.filterer.level.Level(
        min="warning", max="warning"
    )
    warning_handler.filterer = warning_filterer

    sawmill.root.handlers = {
        "error": error_handler,
        "warning": warning_handler
    }

    return error_captured, warning_captured


class Formatter(sawmill.formatter.mustache.Mustache):
    """:term:`Mustache` template to format :class:`logs <sawmill.log.Log>`.
    """

    def __init__(self, template):
        """Initialize with :term:`Mustache` template."""
        self._renderer = pystache.Renderer(escape=lambda value: value)
        super(Formatter, self).__init__(template, batch=False)

    def format(self, logs):
        """Format *logs* for display."""
        data = []

        for log in logs:
            line = self._renderer.render(self.template, log)

            if "level" in log.keys():
                if log["level"] in _COLOR.keys():
                    line = (
                        _COLOR[log["level"]] + line +
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

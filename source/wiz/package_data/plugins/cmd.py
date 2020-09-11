# :coding: utf-8

from __future__ import print_function

import os
import sys
import signal
import subprocess
import tempfile

import wiz.logging
import wiz.shell

#: Unique identifier of the plugin.
IDENTIFIER = "cmd"

# Path to the bash executable on the file system.
EXECUTABLE = "C:\\Windows\\System32\\cmd.exe"


def shell(environment, command=None):
    """Spawn a sub-shell with an *environment* mapping.

    :param environment: Mapping containing environment variables to set in the
        new shell.
    :param command: Mapping of command aliases which should be available in the
        shell.

    """
    logger = wiz.logging.Logger(__name__ + ".shell")

    # Convert entries of environment from unicode to string.
    environment = wiz.shell.convert(environment)

    # NamedTemporaryFile on windows varies from the linux implementation:
    # https://docs.python.org/2/library/tempfile.html
    rcfile = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bat")
    for alias, value in command.items():
        rcfile.write("doskey {0}={1}\n".format(alias, value))
        rcfile.flush()

    if os.path.exists(rcfile.name):
        executable = ["start", EXECUTABLE, "/K", rcfile.name]
    else:
        executable = ["start", EXECUTABLE, "/K"]

    logger.info("Spawn shell: {}".format(executable))

    p = wiz.shell.popen(
        executable,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True
    )

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr

def execute(elements, environment):
    """Run command *elements* within a specific *environment*.

    :param elements: List of command elements to run in the new shell.
    :param environment: Mapping containing environment variables to set in the
        new shell.

    """
    logger = wiz.logging.Logger(__name__ + ".execute")
    logger.info(
        "Start command: {}".format(wiz.utility.combine_command(elements))
    )

    # Convert entries of environment from unicode to string.
    environment = wiz.shell.convert(environment)

    # Substitute environment variables from command line elements.
    elements = [
        wiz.environ.substitute(element, environment) for element in elements
    ]

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    try:
        # Creationflags only exist on windows, explained here:
        # https://docs.python.org/2/library/subprocess.html
        subprocess.call(
            [EXECUTABLE, "/K"] + elements,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            env=environment
        )
    except OSError:
        logger.error(
            "Executable can not be found within resolved "
            "environment [{}]".format(elements[0])
        )
        logger.debug_traceback()


def _cleanup(signum, frame):
    """Exit from python if a process is terminated or interrupted."""
    sys.exit(0)


def register(config):
    """Register shell callbacks."""
    # Only register for Windows.
    if not os.name == 'nt':
        return

    config.setdefault("callback", {})
    config["callback"].setdefault("shell", {})
    config["callback"]["shell"].setdefault(IDENTIFIER, {})
    config["callback"]["shell"][IDENTIFIER]["shell"] = shell
    config["callback"]["shell"][IDENTIFIER]["execute"] = execute

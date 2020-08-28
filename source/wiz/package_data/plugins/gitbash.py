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
IDENTIFIER = "bash"

# Path to the git bash executable on the file system.
EXECUTABLE = "C:\\Program Files\\Git\\git-bash.exe"


def shell(environment, command=None):
    """Spawn a sub-shell with an *environment* mapping.

    :param environment: Environment mapping to spawn the shell with.

    :param command: Mapping of command aliases which should be available in the
        shell.

        .. important:
            Since git-bash does not support handing in a bashrc file into a new
            shell, the global .bashrc needs to be modified to contain these
            lines::

                if [ -f "$BASHRC" ]; then
                    source "$BASHRC"
                fi

    """
    logger = wiz.logging.Logger(__name__ + ".shell")

    if command is None:
        command = {}

    # Convert entries of environment from unicode to string.
    environment = wiz.shell.convert(environment)

    logger.info("Spawn shell: {}".format(EXECUTABLE))

    # NamedTemporaryFile on windows varies from the linux implementation:
    # https://docs.python.org/2/library/tempfile.html
    rcfile = tempfile.NamedTemporaryFile(mode="w", delete=False)
    for alias, value in command.items():
        rcfile.write("alias {0}='{1}'\n".format(alias, value))
        rcfile.flush()

    if os.path.exists(rcfile.name):
        environment["BASHRC"] = rcfile.name

    p = wiz.shell.popen(
        [EXECUTABLE],
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        universal_newlines=True
    )

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr


def execute(elements, environment):
    """Run command *elements* within a specific *environment*.

    :param elements: List of strings constituting the command line to execute
        (e.g. ["app_exe", "--option", "value"])

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
            [EXECUTABLE, "-c"] + elements,
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

    # Only register if executable path exists.
    if not os.path.exists(EXECUTABLE):
        return

    config.setdefault("callback", {})
    config["callback"].setdefault("shell", {})
    config["callback"]["shell"].setdefault(IDENTIFIER, {})
    config["callback"]["shell"][IDENTIFIER]["shell"] = shell
    config["callback"]["shell"][IDENTIFIER]["execute"] = execute

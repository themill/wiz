# :coding: utf-8

from __future__ import print_function

import os
import sys
import select
import subprocess
import tempfile
# import termios
# import tty
# import pty
import signal

import wiz.logging
import wiz.utility
import wiz.symbol


def shell(environment, command=None):
    """Spawn a sub-shell with an *environment* mapping.

    Default shell is Bash.

    *command* is a mapping of command aliases which should be available in the
    shell.

    """
    logger = wiz.logging.Logger(__name__ + ".shell")

    if command is None:
        command = {}

    # TODO: Improve default shell to make it cross platform...
    executable = "/bin/bash"
    logger.info("Spawn shell: {}".format(executable))

    # save original tty setting then set it to raw mode
    # old_tty = termios.tcgetattr(sys.stdin)
    # tty.setraw(sys.stdin.fileno())

    # open pseudo-terminal to interact with subprocess
    # master_fd, slave_fd = pty.openpty()

    # Create temporary rc file for shell aliases for commands
    rcfile = tempfile.NamedTemporaryFile()
    for alias, value in command.items():
        rcfile.write("alias {0}='{1}'\n".format(alias, value))
        rcfile.seek(0)
        rcfile.read()

    if os.path.exists(rcfile.name):
        executable = [executable, "--rcfile", rcfile.name]

    # Run in a new process group to enable job control
    process = subprocess.Popen(
        executable,
        preexec_fn=os.setsid,
        # stdin=slave_fd,
        # stdout=slave_fd,
        # stderr=slave_fd,
        universal_newlines=True,
        env=environment
    )

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    while process.poll() is None:
        pass
        # read_list, write_list, _ = select.select([sys.stdin, master_fd], [], [])
        #
        # if sys.stdin in read_list:
        #     message = os.read(sys.stdin.fileno(), 10240)
        #     os.write(master_fd, message)
        #
        # elif master_fd in read_list:
        #     message = os.read(master_fd, 10240)
        #     if message:
        #         os.write(sys.stdout.fileno(), message)

    # Restore tty settings back
    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)

    # Remove temporary rc file for shell aliases
    rcfile.close()


def execute(elements, environment):
    """Run command *elements* within a specific *environment*."""
    logger = wiz.logging.Logger(__name__ + ".shell")
    logger.info(
        "Start command: {}".format(wiz.utility.combine_command(elements))
    )

    # Substitute environment variables from command line elements.
    elements = [
        wiz.environ.substitute(element, environment) for element in elements
    ]

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    try:
        subprocess.call(elements, env=environment)
    except OSError:
        logger.error(
            "Executable can not be found within resolved "
            "environment [{}]".format(elements[0])
        )
        logger.debug_traceback()


def _cleanup(signum, frame):
    """Exit from python if a process is terminated or interrupted."""
    sys.exit(0)

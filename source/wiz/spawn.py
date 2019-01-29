# :coding: utf-8

from __future__ import print_function

import os
import sys
import select
import subprocess
import distutils.spawn
import termios
import tty
import pty
import signal

import mlog

import wiz.utility
import wiz.symbol


def shell(environment):
    """Spawn a sub-shell with an *environment* mapping.

    Default shell is Bash.

    """
    logger = mlog.Logger(__name__ + ".shell")

    # TODO: Improve default shell to make it cross platform...
    executable = "/bin/bash"
    logger.info("Spawn shell: {}".format(executable))

    # save original tty setting then set it to raw mode
    old_tty = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())

    # open pseudo-terminal to interact with subprocess
    master_fd, slave_fd = pty.openpty()

    # Run in a new process group to enable job control
    process = subprocess.Popen(
        executable,
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True,
        env=environment
    )

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    while process.poll() is None:
        read_list, write_list, _ = select.select([sys.stdin, master_fd], [], [])

        if sys.stdin in read_list:
            message = os.read(sys.stdin.fileno(), 10240)
            os.write(master_fd, message)

        elif master_fd in read_list:
            message = os.read(master_fd, 10240)
            if message:
                os.write(sys.stdout.fileno(), message)

    # restore tty settings back
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)


def execute(elements, environment):
    """Run command *elements* within a specific *environment*."""
    logger = mlog.Logger(__name__ + ".shell")
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
    except OSError as error:
        logger.error(
            "Executable can not be found within resolved "
            "environment [{}]".format(elements[0])
        )
        logger.debug(error, traceback=True)


def _cleanup(signum, frame):
    """Exit from python if a process is terminated or interrupted."""
    sys.exit(0)

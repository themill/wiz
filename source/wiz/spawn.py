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
import functools

import mlog


def shell(environment, shell_type="bash"):
    """Spawn a sub-shell with an *environment* mapping.

    *shell_type* can indicate a specific type of shell. Default is Bash.

    """
    logger = mlog.Logger(__name__ + ".shell")

    # TODO: Improve default shell to make it cross platform...
    default_shell = "/bin/bash"

    executable = distutils.spawn.find_executable(shell_type)
    logger.info("Spawn shell: {}".format(executable))

    # save original tty setting then set it to raw mode
    old_tty = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())

    # open pseudo-terminal to interact with subprocess
    master_fd, slave_fd = pty.openpty()

    # Run in a new process group to enable job control
    process = subprocess.Popen(
        executable or default_shell,
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True,
        env=environment
    )

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    handler = functools.partial(_cleanup, process, logger)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

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


def execute(commands, environment):
    """Run *commands* within a specific *environment*."""
    # Run in a new process group to enable job control
    logger = mlog.Logger(__name__ + ".shell")
    logger.info("Start command: {}".format(" ".join(commands)))

    process = subprocess.Popen(
        commands,
        preexec_fn=os.setsid,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        env=environment
    )

    # Register the cleanup function as handler for SIGINT and SIGTERM.
    handler = functools.partial(_cleanup, process, logger)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    lines_iterator = iter(process.stdout.readline, b"")
    while process.poll() is None:
        for line in lines_iterator:
            _line = line.rstrip()
            print(_line.decode("latin"), end="\r\n")


def _cleanup(process, logger, signum, frame):
    """Kill the sub-process *process* with all children and exit."""
    logger.warning("Kill process [pid: {}]".format(process.pid))
    os.killpg(process.pid, signal.SIGTERM)
    sys.exit(0)

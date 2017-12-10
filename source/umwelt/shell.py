# :coding: utf-8

import os
import sys
import select
import subprocess
import distutils.spawn
import termios
import tty
import pty


def spawn_shell(environment, shell_type="sh"):
    """Spawn a sub-shell."""
    executable = distutils.spawn.find_executable(shell_type)

    # Update the environment to connect to X server within shell
    environment["DISPLAY"] = ":0.0"

    # save original tty setting then set it to raw mode
    old_tty = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())

    # open pseudo-terminal to interact with subprocess
    master_fd, slave_fd = pty.openpty()

    process = subprocess.Popen(
        executable,
        preexec_fn=os.setsid, # Run in a new process group to enable job control
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True,
        env=environment
    )

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

# :coding: utf-8

import os
import sys
import select
import subprocess
import distutils.spawn
import termios
import tty
import pty


def spawn_shell(environment, shell_type="bash"):
    """Spawn a sub-shell."""
    executable = distutils.spawn.find_executable(shell_type)

    # Update environment to preserve important values from current context
    environment["DISPLAY"] = os.environ.get("DISPLAY")
    environment["USER"] = os.environ.get("USER")
    environment["HOME"] = os.environ.get("HOME")
    environment["PATH"] = os.pathsep.join([
        environment.get("PATH", ""),
        "/usr/local/sbin", "/usr/local/bin", "/sbin:/bin",
        "/usr/sbin", "/usr/bin", "/root/bin"
    ])

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

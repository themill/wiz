# :coding: utf-8

import getpass
import os
import socket


def register(config):
    """Register initial environment variables."""
    environ = {
        "USER": getpass.getuser(),
        "HOME": os.path.expanduser("~"),
        "HOSTNAME": socket.gethostname(),
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }

    config.setdefault("environ", {})
    config["environ"].setdefault("initial", {})
    config["environ"]["initial"].update(environ)

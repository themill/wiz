# :coding: utf-8

import getpass
import os
import socket

#: Unique identifier of the plugin.
IDENTIFIER = "environ"


def register(config):
    """Register initial environment variables.

    The initial environment mapping contains basic variables from the external
    environment that can be used by the resolved environment, such as
    the *USER*, the *HOSTNAME* or the *HOME* variables.

    The *PATH* variable is initialized with default values to have access to the
    basic UNIX commands.

    """
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

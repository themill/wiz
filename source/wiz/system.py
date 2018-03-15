# :coding: utf-8

import os
import sys
import platform

import wiz.exception


def query():
    """Return system mapping.

    Raise :exc:`wiz.exception.UnsupportedPlatform` if platform is not supported.

    """
    name = platform.system().lower()
    if name == "linux":
        return query_linux_mapping()
    elif name == "darwin":
        return query_mac_mapping()
    elif name == "windows":
        return query_windows_mapping()

    raise wiz.exception.UnsupportedPlatform(name)


def query_linux_mapping():
    """Return Linux system mapping."""
    distribution, version, _ = platform.linux_distribution(
        full_distribution_name=False
    )

    return {
        "platform": "linux",
        "arch": platform.machine(),
        "os_version": "{}=={}".format(distribution, version)
    }


def query_mac_mapping():
    """Return mac system mapping."""
    return {
        "platform": "mac",
        "arch": platform.machine(),
        "os_version": "mac=={}".format(platform.mac_ver()[0])
    }


def query_windows_mapping():
    """Return windows system mapping."""
    architecture = platform.machine(),

    # Work around this bug: https://bugs.python.org/issue7860
    if os.name == "nt" and sys.version_info[:2] < (2, 7):
        architecture = os.environ.get(
            "PROCESSOR_ARCHITEW6432", os.environ.get("PROCESSOR_ARCHITECTURE")
        )

    return {
        "platform": "windows",
        "arch": architecture,
        "os_version": "windows=={}".format(platform.win32_ver()[1])
    }

# :coding: utf-8

import os
import sys
import platform

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.exception


def query():
    """Return system mapping.

    The mapping should be in the form of::

        {
            "platform": "linux",
            "arch": "x86_64",
            "os": {
                "name": "centos",
                "version": "7.3.161"
            }
        }

    Raise :exc:`wiz.exception.UnsupportedPlatform` if platform is not supported.

    """
    name = platform.system().lower()

    try:
        if name == "linux":
            return query_linux_mapping()
        elif name == "darwin":
            return query_mac_mapping()
        elif name == "windows":
            return query_windows_mapping()

    except InvalidVersion as error:
        raise wiz.exception.IncorrectDefinition(
            "The operating system version found seems incorrect [{}]".format(
                error
            )
        )

    raise wiz.exception.UnsupportedPlatform(name)


def query_linux_mapping():
    """Return Linux system mapping."""
    distribution, version, _ = platform.linux_distribution(
        full_distribution_name=False
    )

    return {
        "platform": "linux",
        "arch": platform.machine(),
        "os": {
            "name": distribution,
            "version": Version(version)
        }
    }


def query_mac_mapping():
    """Return mac system mapping."""
    return {
        "platform": "mac_os",
        "arch": platform.machine(),
        "os": {
            "name": "mac_os",
            "version": Version(platform.mac_ver()[0])
        }
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
        "os": {
            "name": "windows",
            "version": Version(platform.win32_ver()[1])
        }
    }


def validate(definition, platform_identifier, arch, os_mapping):
    """Validate *definition* against system *mapping*.

    *definition* should be a :class:`wiz.definition.Definition` instances.

    *platform_identifier* should be "linux", "mac_os" or "windows".

    *arch* should be "x86_64" or "i386".

    *os_mapping* should be a mapping in the form of::

        {
            "name": "centos",
            "version": <Version(7.3.161)>
        }

    """
    system = definition.system

    # If no system is set on the definition, it is considered compatible with
    # any platform.
    if len(system) == 0:
        return True

    # Filter platform if necessary.
    if system.get("platform", platform_identifier) != platform_identifier:
        return False

    # Filter architecture if necessary.
    if system.get("arch", arch) != arch:
        return False

    # Filter operating system version if necessary.
    os_system = system.get("os")
    if os_system is not None:
        try:
            os_requirement = Requirement(os_system)
        except InvalidRequirement:
            raise wiz.exception.IncorrectDefinition(
                "The operating system requirement is incorrect: {}".format(
                    os_system
                )
            )

        if os_requirement.name != os_mapping["name"]:
            return False

        if os_mapping["version"] not in os_requirement.specifier:
            return False

    return True

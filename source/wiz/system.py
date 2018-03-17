# :coding: utf-8

import platform

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.exception


#: Operating System group mapping
OS_MAPPING = {
    "el": ["centos", "redhat"]
}


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
            return query_linux()
        elif name == "darwin":
            return query_mac()
        elif name == "windows":
            return query_windows()

    except InvalidVersion as error:
        raise wiz.exception.IncorrectDefinition(
            "The operating system version found seems incorrect [{}]".format(
                error
            )
        )

    raise wiz.exception.UnsupportedPlatform(name)


def query_linux():
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


def query_mac():
    """Return mac system mapping."""
    return {
        "platform": "mac",
        "arch": platform.machine(),
        "os": {
            "name": "mac",
            "version": Version(platform.mac_ver()[0])
        }
    }


def query_windows():
    """Return windows system mapping.

    .. warning::

        The Windows versions superior to 8 will not be recognised properly with
        a Python version under 2.7.11

        https://hg.python.org/cpython/raw-file/53d30ab403f1/Misc/NEWS

        Also a bug as been introduced in Python 2.7.11 that prevent the
        recognition of old Windows version

        https://bugs.python.org/issue26513

    """
    return {
        "platform": "windows",
        "arch": platform.machine(),
        "os": {
            "name": "windows",
            "version": Version(platform.win32_ver()[1])
        }
    }


def validate(definition, system_mapping):
    """Validate *definition* against system *mapping*.

    *definition* should be a :class:`wiz.definition.Definition` instances.

    The *system_mapping* should be in the form of::

        {
            "platform": "linux",
            "arch": "x86_64",
            "os": {
                "name": "centos",
                "version": <Version(7.3.161)>
            }
        }

    """
    system = definition.system

    # If no system is set on the definition, it is considered compatible with
    # any platform.
    if len(system) == 0:
        return True

    # Filter platform if necessary.
    platform_identifier = system_mapping.get("platform")
    if system.get("platform", platform_identifier) != platform_identifier:
        return False

    # Filter architecture if necessary.
    architecture = system_mapping.get("arch")
    if system.get("arch", architecture) != architecture:
        return False

    # Filter operating system version if necessary.
    os_system = system.get("os")
    if os_system is not None:
        try:
            requirement = Requirement(os_system)
        except InvalidRequirement:
            raise wiz.exception.IncorrectDefinition(
                "The operating system requirement is incorrect: {}".format(
                    os_system
                )
            )

        os_mapping = system_mapping.get("os", {})

        if not (
            requirement.name == os_mapping.get("name") or
            os_mapping.get("name") in OS_MAPPING.get(requirement.name, [])
        ):
            return False

        if os_mapping.get("version") not in requirement.specifier:
            return False

    return True

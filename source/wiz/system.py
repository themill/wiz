# :coding: utf-8

import platform as _platform

import distro

import wiz.exception
import wiz.history
import wiz.symbol
import wiz.utility

#: Operating System group mapping
OS_MAPPING = {
    "el": ["centos", "redhat"]
}


def query(platform=None, architecture=None, os_name=None, os_version=None):
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

    :param platform: Indicate a platform identifier which would override the
        platform identifier queried. Default is None.

    :param architecture: Indicate an architecture identifier which would
        override the architecture identifier queried. Default is None.

    :param os_name: Indicate an operating system identifier which would override
        the operating system identifier queried. Default is None.

    :param os_version: Indicate an operating system version which would override
        the operating system version queried. Default is None.

    :return: System mapping.

    :raise: :exc:`wiz.exception.IncorrectSystem` if current system could not
        be identified or is not supported.

    """
    name = _platform.system().lower()

    try:
        if name == "linux":
            mapping = query_linux()
        elif name == "darwin":
            mapping = query_mac()
        elif name == "windows":
            mapping = query_windows()
        else:
            raise wiz.exception.UnsupportedPlatform(name)

    except wiz.exception.VersionError as error:
        raise wiz.exception.CurrentSystemError(
            "The operating system version found seems incorrect "
            "[{}]".format(error)
        )

    if platform is not None:
        mapping["platform"] = platform

    if architecture is not None:
        mapping["arch"] = architecture

    if os_name is not None:
        mapping["os"]["name"] = os_name

    if os_version is not None:
        mapping["os"]["version"] = os_version

    wiz.history.record_action(
        wiz.symbol.SYSTEM_IDENTIFICATION_ACTION, system=mapping
    )

    return mapping


def query_linux():
    """Return Linux system mapping.

    :return: Mapping in the form of
        ::

            {
                "platform": "linux",
                "arch": "x86_64",
                "os": {
                    "name": "centos",
                    "version": "7.3.161"
                }
            }

    """
    distribution, version, _ = distro.linux_distribution(
        full_distribution_name=False
    )

    return {
        "platform": "linux",
        "arch": _platform.machine(),
        "os": {
            "name": distribution,
            "version": wiz.utility.get_version(version)
        }
    }


def query_mac():
    """Return mac system mapping.

    :return: Mapping in the form of
        ::

            {
                "platform": "mac",
                "arch": "x86_64",
                "os": {
                    "name": "mac",
                    "version": "10.15.5"
                }
            }

    """
    return {
        "platform": "mac",
        "arch": _platform.machine(),
        "os": {
            "name": "mac",
            "version": wiz.utility.get_version(_platform.mac_ver()[0])
        }
    }


def query_windows():
    """Return windows system mapping.

    :return: Mapping in the form of
        ::

            {
                "platform": "windows",
                "arch": "x86_64",
                "os": {
                    "name": "windows",
                    "version": "10.0.10240"
                }
            }

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
        "arch": _platform.machine(),
        "os": {
            "name": "windows",
            "version": wiz.utility.get_version(_platform.win32_ver()[1])
        }
    }


def validate(definition, system_mapping):
    """Validate *definition* against system *mapping*.

    :param definition: Instance of :class:`wiz.definition.Definition`.

    :param system_mapping: System mapping as returned by :func:`query`.

    :return: Boolean value.

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
            requirement = wiz.utility.get_requirement(os_system)
        except wiz.exception.RequirementError:
            raise wiz.exception.DefinitionError(
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

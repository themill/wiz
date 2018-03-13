# :coding: utf-8

import os

from wiz import __version__
import wiz.graph
import wiz.symbol
import wiz.exception


def get(requirement, environment_mapping):
    """Get best matching environment version for *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    :exc:`wiz.exception.RequestNotFound` is raised if the
    requirement can not be resolved.

    """
    if requirement.name not in environment_mapping:
        raise wiz.exception.RequestNotFound(requirement)

    environment = None

    # Sort the environment versions so that the highest one is first.
    versions = sorted(
        environment_mapping[requirement.name].keys(), reverse=True
    )

    # Get the best matching environment.
    for version in versions:
        _environment = environment_mapping[requirement.name][version]
        if _environment.version in requirement.specifier:
            environment = _environment
            break

    if environment is None:
        raise wiz.exception.RequestNotFound(requirement)

    return environment


def initiate_data(data_mapping=None):
    """Return the initiate environment data to augment.

    The initial environment contains basic variables from the external
    environment that can be used by the resolved environment, such as
    the *USER* or the *HOME* variables.

    The other variable added are:

    * DISPLAY:
        This variable is necessary to open user interface within the current
        X display name.

    * PATH:
        This variable is initialised with default values to have access to the
        basic UNIX commands.

    *environ_mapping* can be a custom environment mapping which will be added
    to the initial environment.

    """
    environ = {
        "WIZ_VERSION": __version__,
        "USER": os.environ.get("USER"),
        "LOGNAME": os.environ.get("LOGNAME"),
        "HOME": os.environ.get("HOME"),
        "DISPLAY": os.environ.get("DISPLAY"),
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }

    if data_mapping is not None:
        environ.update(**data_mapping)

    return environ

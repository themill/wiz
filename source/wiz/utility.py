# :coding: utf-8

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.exception


def _display_requirement(_requirement):
    """Replace the string conversion for *requirement* to increase readability.
    """
    content = _requirement.name

    if len(_requirement.specifier) > 0:
        content += " " + ", ".join(sorted([
            str(specifier) for specifier in _requirement.specifier
        ], reverse=True))

    return content


#: Monkeypatch magic method to improve readability of serialized item.
Requirement.__str__ = _display_requirement


def requirement(content):
    """Return the corresponding requirement instance from *content*.

    The requirement returned is a :class:`packaging.requirements.Requirement`
    instance.

    *content* must be a string which represent a requirement, with or without
    version specifier or variant (e.g. "maya", "nuke >= 10, < 11",
    "ldpk-nuke[10.0]").

    Raises :exc:`wiz.exception.InvalidRequirement` if the requirement is
    incorrect.

    """
    try:
        return Requirement(content)
    except InvalidRequirement:
        raise wiz.exception.InvalidRequirement(
            "The requirement '{}' is incorrect".format(content)
        )


def version(content):
    """Return the corresponding version instance from *content*.

    The version returned is a :class:`packaging.version.Version` instance.

    *content* must be a string which represent a version (e.g. "2018", "0.1.0").

    Raises :exc:`wiz.exception.InvalidVersion` if the version is incorrect.

    """
    try:
        return Version(content)
    except InvalidVersion:
        raise wiz.exception.InvalidVersion(
            "The version '{}' is incorrect".format(content)
        )

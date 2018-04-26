# :coding: utf-8

import base64
import json
import zlib

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.mapping
import wiz.exception


def _display_requirement(_requirement):
    """Improve readability when displaying Requirement instance.

    Before::

        >>> Requirement("nuke>=10,<11")
        <Requirement('nuke<11,>=10')>

    After::

        >>> Requirement("nuke>=10,<11")
        <Requirement('nuke >=10, <11')>

    """
    content = _requirement.name

    if len(_requirement.specifier) > 0:
        content += " " + ", ".join(sorted([
            str(specifier) for specifier in _requirement.specifier
        ], reverse=True))

    return content


#: Monkeypatch magic method to improve readability of serialized item.
Requirement.__str__ = _display_requirement


def _compare_requirement(_requirement, other):
    """Improve comparison between Requirement instances.

    Before::

        >>> Requirement("nuke>=10,<11") == Requirement("nuke>=10,<11")
        False

    After::

        >>> Requirement("nuke>=10,<11") == Requirement("nuke>=10,<11")
        True

     """
    if isinstance(other, Requirement):
        return str(_requirement) == str(other)
    return False


#: Monkeypatch magic method to allow comparison between instances.
Requirement.__eq__ = _compare_requirement


def get_requirement(content):
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


def get_version(content):
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


def encode(element):
    """Return serialized and encoded *element*.

    *element* is serialized first, then encoded into :term:`base64`.

    Raises :exc:`TypeError` if *element* is not JSON serializable.

    """
    return base64.b64encode(zlib.compress(json.dumps(element)))


def decode(element):
    """Return deserialized and decoded *element*.

    *element* is decoded first from :term:`base64`, then deserialized.

    Raises :exc:`TypeError` if *element* cannot be decoded or deserialized..

    """
    return json.loads(zlib.decompress(base64.b64decode(element)))


def serialize(element):
    """Return recursively serialized *element*.

    *element* can be a of any types (:class:`Mapping`, dict, list, ...)

    """
    if isinstance(element, list):
        return [serialize(item) for item in element]

    elif isinstance(element, dict):
        return {_id: serialize(item) for _id, item in element.items()}

    elif isinstance(element, wiz.mapping.Mapping):
        return element.to_dict(serialize_content=True)

    return str(element)

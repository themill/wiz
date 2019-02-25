# :coding: utf-8

import re
import pipes
import json
import zlib
import base64
import hashlib
import colorama

import packaging.requirements
from packaging.requirements import (
    L, Combine, Word, ZeroOrMore, ALPHANUM, Optional, EXTRAS,
    URL_AND_MARKER, VERSION_AND_MARKER, stringStart, stringEnd
)

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.symbol
import wiz.mapping
import wiz.exception


# Extend requirement's expression to allow namespace separators as a valid
# identifier (e.g. "foo::test", "::test").
PUNCTUATION = Word("-_.")
NAME = ALPHANUM + ZeroOrMore(ALPHANUM | (ZeroOrMore(PUNCTUATION) + ALPHANUM))
NAME_SEPARATOR = L(wiz.symbol.NAMESPACE_SEPARATOR)
IDENTIFIER = Combine(
    Optional(Optional(NAME) + NAME_SEPARATOR) + NAME
)

packaging.requirements.REQUIREMENT = (
    stringStart + IDENTIFIER("name") + Optional(EXTRAS)
    + (URL_AND_MARKER | VERSION_AND_MARKER) + stringEnd
)


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

    variant = ",".join(_requirement.extras)
    if len(variant) > 0:
        content += "[{}]".format(variant)

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


def compute_label(definition):
    """Return unique label for *definition*.

    The name should be in the form of::

        "'foo'"
        "'bar' [0.1.0]"
        "'baz' [0.2.0] (linux : el =! 7)"
        "'bim' (linux : el >= 6, < 7)"

    *definition* should be a :class:`wiz.definition.Definition` instance.

    """
    label = "'{}'".format(definition.qualified_identifier)

    if definition.get("version"):
        label += " [{}]".format(definition.version)

    if definition.get("system"):
        system_identifier = compute_system_label(definition)
        label += " ({})".format(system_identifier)

    return label


def compute_system_label(definition):
    """Return unique system label from *definition*.

    The system identifier should be in the form of::

        "linux : x86_64 : el >= 7, < 8"
        "centos >= 7, < 8"
        "x86_64 : el >= 7, < 8"
        "windows"

    *definition* should be a :class:`wiz.definition.Definition` instance.

    """
    elements = [
        definition.system.get(element)
        for element in ["platform", "arch", "os"]
        if definition.system.get(element) is not None
    ]
    return " : ".join(elements) or "noarch"


def compute_file_name(definition):
    """Return unique file name from *definition*.

    The file name should be in the form of::

        "foo.json"
        "foo-0.1.0.json"
        "foo-0.1.0-M2Uq9Esezm-m00VeWkTzkQIu3T4.json"

    *definition* should be a :class:`wiz.definition.Definition` instance.

    """
    name = definition.identifier

    if definition.get("version"):
        name += "-{}".format(definition.version)

    if definition.get("system"):
        system_identifier = wiz.utility.compute_system_label(definition)
        encoded = base64.urlsafe_b64encode(
            hashlib.sha1(re.sub(r"(\s+|:+)", "", system_identifier)).digest()
        )
        name += "-{}".format(encoded.rstrip("="))

    return "{}.json".format(name)


def combine_command(elements):
    """Return command *elements* as a string.

    Example::

        >>> combine_command(
        ...     ['python2.7', '-c', 'import os; print(os.environ["HOME"])'])
        ... )

        python2.7 -c 'import os; print(os.environ["HOME"])'

    """
    return " ".join([pipes.quote(element) for element in elements])


def colored(message, color):
    """Return colored *message* according to color *name*.

    Available color names are: "black", "red", "green", "yellow", "blue",
    "magenta", "cyan" and "white".

    """
    return (
        getattr(colorama.Fore, color.upper()) + message +
        colorama.Style.RESET_ALL
    )

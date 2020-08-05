# :coding: utf-8

import base64
import collections
import hashlib
import json
import pipes
import re
import zlib

import colorama
from packaging.requirements import InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.exception
import wiz.mapping
import wiz.symbol
from _requirement import Requirement

# Arbitrary number which indicates a very high version number
_INFINITY_VERSION = 9999


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


def is_overlapping(requirement1, requirement2):
    """Indicate whether requirements are overlapping.

    A requirement is overlapping with another one if their intersection of
    version ranges are not empty.

    Example::

        >>> is_overlapping(Requirement("foo >= 10"), Requirement("foo < 9"))
        True

        >>> is_overlapping(Requirement("foo >= 10"), Requirement("foo < 8"))
        False

    *requirement1* and *requirement2* should be instances of
    :class:`packaging.requirements.Requirement`.

    Raise :exc:`wiz.exception.GraphResolutionError` if requirements cannot
    be compared.

    """
    if requirement1.name != requirement2.name:
        raise wiz.exception.GraphResolutionError(
            "Impossible to compare requirements with different names "
            "['{}' and '{}'].".format(requirement1.name, requirement2.name)
        )

    r1 = extract_version_ranges(requirement1)
    r2 = extract_version_ranges(requirement2)
    return (
        (r2[-1][1] is None or r2[-1][1] >= r1[0][0]) and
        (r1[-1][1] is None or r1[-1][1] >= r2[0][0])
    )


def extract_version_ranges(requirement):
    """Extract version ranges from *requirement*.

    A list of version tuples is returned

    Requirement could contain the following specifiers:

    * `Compatible release
      <https://www.python.org/dev/peps/pep-0440/#compatible-release>`_
    * `Version matching
      <https://www.python.org/dev/peps/pep-0440/#version-matching>`_
    * `Version exclusion
      <https://www.python.org/dev/peps/pep-0440/#version-exclusion>`_
    * `Inclusive ordered comparison
      <https://www.python.org/dev/peps/pep-0440/#inclusive-ordered-comparison>`_
    * `Exclusive ordered comparison
      <https://www.python.org/dev/peps/pep-0440/#exclusive-ordered-comparison>`_

    Example::

        >>> extract_version_ranges(Requirement("foo"))
        [(None, None)]

        >>> extract_version_ranges(Requirement("foo==2.1.1"))
        [((2, 1, 1), (2, 1, 1))]

        >>> extract_version_ranges(Requirement("foo!=2.1.1"))
        [(None, (2, 1, 0, 9999)), ((2, 1, 1, 1), None)]

        >>> extract_version_ranges(Requirement("foo ==2.*"))
        [((2,), (2, 9999))]

        >>> extract_version_ranges(Requirement("foo >= 2, < 3"))
        [((2,), (2, 9999))]

    *requirement* should be an instance of
    :class:`packaging.requirements.Requirement`.

    :exc:`wiz.exception.InvalidVersion` is raised if the version extracted from
    the specifier is incorrect.

    :exc:`wiz.exception.InvalidRequirement` is raised if the specifier operator
    is not accepted or if the requirement does not allow any versions to be
    reached.

    """
    version_ranges = [(None, None)]

    for specifier in requirement.specifier:
        # Extract version number.
        _version = wiz.utility.get_version(
            re.sub(r"\.\*$", "", specifier.version)
        ).release

        # Update maximum according to operator.
        if specifier.operator == ">=":
            _update_minimum_version(_version, version_ranges)

        elif specifier.operator == "<=":
            _update_maximum_version(_version, version_ranges)

        elif specifier.operator == ">":
            _min_version = _increment_version(_version)
            _update_minimum_version(_min_version, version_ranges)

        elif specifier.operator == "<":
            _max_version = _decrement_version(_version)
            _update_maximum_version(_max_version, version_ranges)

        elif specifier.operator == "~=":
            _max_version = _increment_version(_version, delta=_INFINITY_VERSION)
            _update_minimum_version(_version, version_ranges)
            _update_maximum_version(_max_version, version_ranges)

        elif specifier.operator == "==" and specifier.version.endswith(".*"):
            _max_version = _increment_version(_version, delta=_INFINITY_VERSION)
            _update_minimum_version(_version, version_ranges)
            _update_maximum_version(_max_version, version_ranges)

        elif specifier.operator == "==":
            _update_minimum_version(_version, version_ranges)
            _update_maximum_version(_version, version_ranges)

        elif specifier.operator == "!=" and specifier.version.endswith(".*"):
            _min_version = _decrement_version(_version)
            _max_version = _increment_version(_version, add_subversion=False)
            _update_version_ranges((_min_version, _max_version), version_ranges)

        elif specifier.operator == "!=":
            _min_version = _decrement_version(_version)
            _max_version = _increment_version(_version)
            _update_version_ranges((_min_version, _max_version), version_ranges)

        else:
            raise wiz.exception.InvalidRequirement(
                "Operator '{}' is not accepted for requirement '{}'".format(
                    specifier.operator, requirement
                )
            )

    return version_ranges


def _update_maximum_version(version, ranges):
    """Update version *ranges* with maximum *version*.

    *version* should be a version release tuple (e.g. (1,2,3)).

    *ranges* should be an ordered list of tuples containing two
    ordered version release tuples (e.g [((1,2,3), (1,3,0)), (1,3,3), (1,4))]).

    Example::

        >>> ranges = [((1,2,3), (1,3,0)), ((1,3,3), (1,4))]
        >>> _update_maximum_version((1, 2, 3), ranges)
        >>> print(ranges)
        [((1, 2, 3), (1, 2, 3))]

    """
    _ranges = []

    if ranges[0][0] is not None and version < ranges[0][0]:
        raise wiz.exception.InvalidRequirement(
            "The requirement is incorrect as maximum value '{}' cannot be set"
            "when minimum value is '{}'.".format(
                ".".join(str(v) for v in version),
                ".".join(str(v) for v in ranges[-1][1])
            )
        )

    for start_version, end_version in ranges:
        if not end_version or end_version >= version:
            _ranges.append((start_version, version))
            break
        _ranges.append((start_version, end_version))

    # Mutated input ranges
    ranges[:] = _ranges


def _update_minimum_version(version, ranges):
    """Update version *ranges* with minimum *version*.

    *version* should be a version release tuple (e.g. (1,2,3)).

    *ranges* should be an ordered list of tuples containing two
    ordered version release tuples (e.g [((1,2,3), (1,3,0)), (1,3,3), (1,4))).

    Example::

        >>> ranges = [((1,2,3), (1,3,0)), ((1,3,3), (1,4))]
        >>> _update_minimum_version((1, 3, 3), ranges)
        >>> print(ranges)
        [((1, 3, 3), (1, 4))]

    """
    _ranges = []

    if ranges[-1][1] is not None and version > ranges[-1][1]:
        raise wiz.exception.InvalidRequirement(
            "The requirement is incorrect as minimum value '{}' cannot be set"
            "when maximum value is '{}'.".format(
                ".".join(str(v) for v in version),
                ".".join(str(v) for v in ranges[-1][1])
            )
        )

    for start_version, end_version in reversed(ranges):
        if not start_version or start_version <= version:
            _ranges = [(version, end_version)] + _ranges
            break
        _ranges = [(start_version, end_version)] + _ranges

    # Mutated input ranges
    ranges[:] = _ranges


def _update_version_ranges(excluded, ranges):
    """Update version *ranges* from excluded *version_range*.

    *excluded* should be a tuple containing two ordered version release
    tuples (e.g. ((1,2,3), (1,3,0))). These two versions are included in the
    *ranges*, but all versions in between should be excluded.

    *ranges* should be an ordered list of tuples containing two
    ordered version release tuples (e.g [((1,2,3), (1,3,0)), (1,3,3), (1,4))).

    Example::

        >>> ranges = [((1,2,3), (1,3,0)), ((1,3,3), (1,4))]
        >>> _update_version_ranges(((1,2,3), (1,3,3)), ranges)
        >>> print(ranges)
        [((1, 2, 3), (1, 2, 3)), ((1, 3, 3), (1, 4))]

    """
    _ranges = []

    for r in ranges:
        out_before = r[0] is not None and r[0] > excluded[1]
        out_after = r[1] is not None and r[1] < excluded[0]

        # Exclusion zone is outside of range.
        if out_before or out_after:
            _ranges.append(r)
            continue

        r0_excluded = r[0] is not None and r[0] > excluded[0]
        r1_excluded = r[1] is not None and r[1] < excluded[1]

        # Exclusion zone covers all range.
        if r0_excluded and r1_excluded:
            continue

        # Exclusion zone cover start of range only.
        elif r0_excluded and not r1_excluded:
            _ranges.append((excluded[1], r[1]))

        # Exclusion zone cover end of range only.
        elif not r0_excluded and r1_excluded:
            _ranges.append((r[0], excluded[0]))

        # Exclusion zone cover middle of range.
        elif not r0_excluded and not r1_excluded:
            _ranges.append((r[0], excluded[0]))
            _ranges.append((excluded[1], r[1]))

    if len(_ranges) == 0:
        raise wiz.exception.InvalidRequirement(
            "The requirement is incorrect as excluded version range '{}-{}' "
            "makes all other versions unreachable.".format(
                ".".join(str(v) for v in excluded[0]),
                ".".join(str(v) for v in excluded[1]),
            )
        )

    # Mutated input ranges
    ranges[:] = _ranges


def _increment_version(version, delta=1, add_subversion=True):
    """Increment *version*.

    This will attempt to increase to the nearest possible version tuple.

    *version* should be a version release tuple (e.g. (1, 2, 3)).

    *delta* should be the number to add to the minimal the *version*. Default
    is 1.

    *add_subversion* indicates whether a sub-version should be used instead
    of only increasing the minimal release version. Default is True.

    Example::

        >>> _increment_version((1, 2, 0))
        (1, 2, 0, 1)

        >>> _increment_version((1, 2, 0), add_subversion=False)
        (1, 2, 1)

        >>> _increment_version((1, 1, 1), delta=3)
        (1, 1, 1, 3)

    """
    if not add_subversion:
        return version[:-1] + (version[-1] + delta,)
    return version + (delta,)


def _decrement_version(version):
    """Decrement *version*.

    This will attempt to decrease to the nearest possible version tuple.

    *version* should be a version release tuple (e.g. (1, 2, 3)).

    Example::

        >>> _decrement_version((1,))
        (0, 9999)

        >>> _decrement_version((1, 0, 0))
        (1, 9999)

        >>> _decrement_version((1, 2, 0))
        (1, 1, 9999)

        >>> _decrement_version((1, 1, 1))
        (1, 1, 0, 9999)

    """
    index = -1
    while version[index] == 0:
        index -= 1

    return version[:index] + (version[index] - 1, _INFINITY_VERSION)


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


def colored_text(message, color):
    """Return colored *message* according to color *name*.

    Available color names are: "black", "red", "green", "yellow", "blue",
    "magenta", "cyan" and "white".

    """
    return (
        getattr(colorama.Fore, color.upper()) + message +
        colorama.Style.RESET_ALL
    )


def deep_update(mapping1, mapping2):
    """Recursively update *mapping1* from *mapping2*.

    Contrary to :meth:`dict.update`, this function will attempt to update
    sub-dictionaries defined in both mappings instead of overwriting the value
    defined in *mapping1*::

        >>> deep_update({"A": {"B": 2}}, {"A": {"C": 3}})
        {"A": {"B": 2, "C": 3}}

    :param mapping1: Mapping to update

    :param mapping2: Mapping to update *mapping1* from

    :return: *mapping1* mutated.

    .. note::

        *mapping1* will be mutated, but *mapping2* will not.

    """
    for key, value in mapping2.items():
        if isinstance(value, collections.Mapping):
            mapping1[key] = deep_update(mapping1.get(key, {}), value)
        else:
            mapping1[key] = value
    return mapping1

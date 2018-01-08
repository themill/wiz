# :coding: utf-8

import os
import collections
import json

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion
import mlog


def fetch_definition_mapping(paths, max_depth=None):
    """Return mapping from all environment definitions available under *paths*.

    :func:`discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    mapping = dict()

    for definition in discover(paths, max_depth=max_depth):
        mapping.setdefault(definition.identifier, [])
        mapping[definition.identifier].append(definition)

    return mapping


def search_definitions(requirement, paths, max_depth=None):
    """Return mapping from environment definitions matching *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    :func:`~umwelt.definition.discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".search_definitions")
    logger.info(
        "Search environment definition definitions matching '{}'"
        .format(requirement)
    )

    mapping = dict()

    for definition in discover(paths, max_depth=max_depth):
        if (
            requirement.name.lower() in definition.identifier.lower() or
            requirement.name.lower() in definition.description.lower()
        ):
            if definition.version in requirement.specifier:
                mapping.setdefault(definition.identifier, [])
                mapping[definition.identifier].append(definition)

    return mapping


def get(requirement, definition_mapping):
    """Get fittest :class:`Definition` instance for *definition_specifier*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier.

    :exc:`packaging.requirements.InvalidRequirement` is raised if the
    requirement specifier is incorrect.

    """
    if requirement.name not in definition_mapping:
        raise RuntimeError(
            "No definition identified as {!r} has been found."
            .format(requirement.name)
        )

    required_definition = None

    # Sort the definition so that the fittest highest version is loaded first.
    sorted_definitions = sorted(
        definition_mapping[requirement.name],
        key=lambda d: d.version, reverse=True
    )

    for definition in sorted_definitions:
        if definition.version in requirement.specifier:
            required_definition = definition
            break

    if required_definition is None:
        raise RuntimeError(
            "No definition has been found for '{}'."
            .format(requirement)
        )

    if len(requirement.extras) > 0:
        variant = next(iter(requirement.extras))

        variant_mapping = required_definition.get("variant", {})

        if variant not in variant_mapping.keys():
            raise RuntimeError(
                "The variant '{}' has not been found for '{}'.".format(
                    variant, requirement
                )
            )

        required_definition.update(
            combine(variant_mapping[variant], required_definition)
        )

    return required_definition


def combine(definition1, definition2):
    """Return combined mapping from *definition1* and *definition2*.

    The final mapping will only contain the 'data' and 'requirement' keywords.

    """
    definition = {"data": {}, "requirement": []}

    # Extract and combine data from definitions
    data1 = definition1.get("data", {})
    data2 = definition2.get("data", {})

    for key in set(data1.keys() + data2.keys()):
        value1 = data1.get(key)
        value2 = data2.get(key)

        # The keyword must not have a value in the two environment, unless if
        # it is a list that can be combined.
        if value1 is not None and value2 is not None:
            if not isinstance(value1, list) or not isinstance(value2, list):
                raise RuntimeError(
                    "Overriding environment variable per definition is "
                    "forbidden\n"
                    " - {definition1}: {key}={value1!r}\n"
                    " - {definition2}: {key}={value2!r}\n".format(
                        key=key, value1=value1, value2=value2,
                        definition1=definition1.identifier,
                        definition2=definition2.identifier,
                    )
                )

            definition["data"][key] = value1 + value2

        # Otherwise simply set the valid value
        else:
            definition["data"][key] = value1 or value2

    # Extract and combine requirements from definitions
    requirement1 = definition1.get("requirement", [])
    requirement2 = definition2.get("requirement", [])

    definition["requirement"] = requirement1 + requirement2

    return definition


def discover(paths, max_depth=None):
    """Discover and yield environment definitions found under *paths*.

    If *max_depth* is None, search all sub-trees under each path for
    environment files in JSON format. Otherwise, only search up to *max_depth*
    under each path. A *max_depth* of 0 should only search directly under the
    specified paths.

    """
    logger = mlog.Logger(__name__ + ".discover")

    for path in paths:
        # Ignore empty paths that could resolve to current directory.
        path = path.strip()
        if not path:
            logger.debug("Skipping empty path.")
            continue

        path = os.path.abspath(path)
        logger.debug(
            "Searching under {!r} for environment definition files."
            .format(path)
        )
        initial_depth = path.rstrip(os.sep).count(os.sep)
        for base, _, filenames in os.walk(path):
            depth = base.count(os.sep)
            if max_depth is not None and (depth - initial_depth) > max_depth:
                continue

            for filename in filenames:
                _, extension = os.path.splitext(filename)
                if extension != ".json":
                    continue

                environment_path = os.path.join(base, filename)
                logger.debug(
                    "Discovered environment definition file {!r}.".format(
                        environment_path
                    )
                )

                try:
                    environment = load(environment_path)
                except (
                    IOError, ValueError, TypeError,
                    InvalidRequirement, InvalidVersion
                ):
                    logger.warning(
                        "Error occurred trying to load environment definition "
                        "from {!r}".format(environment_path),
                        traceback=True
                    )
                    continue
                else:
                    logger.debug(
                        "Loaded environment definition {!r} from {!r}."
                        .format(environment.identifier, environment_path)
                    )
                    yield environment


def load(path):
    """Load and return :class:`Definition` from *path*."""
    with open(path, "r") as stream:
        definition_data = json.load(stream)

        # TODO: Validate with JSON-Schema.

        definition = Definition(**definition_data)
        definition["version"] = Version(definition.version)
        definition["requirement"] = [
            Requirement(requirement) for requirement
            in definition.get("requirement", [])
        ]

        if "variant" in definition.keys():
            for variant_definition in definition["variant"].values():
                variant_definition["requirement"] = [
                    Requirement(requirement) for requirement
                    in variant_definition.get("requirement", [])
                ]

        return definition


class Definition(collections.MutableMapping):
    """Environment Definition."""

    def __init__(self, *args, **kwargs):
        """Initialise environment definition."""
        super(Definition, self).__init__()
        self._mapping = {}
        self.update(*args, **kwargs)

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier", "unknown")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    @property
    def version(self):
        """Return version."""
        return self.get("version", "unknown")

    def __str__(self):
        """Return string representation."""
        return "{}({!r}, {!r})".format(
            self.__class__.__name__, self.identifier, self._mapping
        )

    def __getitem__(self, key):
        """Return value for *key*."""
        return self._mapping[key]

    def __setitem__(self, key, value):
        """Set *value* for *key*."""
        self._mapping[key] = value

    def __delitem__(self, key):
        """Delete *key*."""
        del self._mapping[key]

    def __iter__(self):
        """Iterate over all keys."""
        for key in self._mapping:
            yield key

    def __len__(self):
        """Return count of keys."""
        return len(self._mapping)

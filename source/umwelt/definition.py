# :coding: utf-8

import os
import collections
import json

from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion
import mlog

import umwelt.environment


def fetch_definition_mapping(paths, max_depth=None):
    """Return mapping from all environment definitions available under *paths*.

    :func:`discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    mapping = dict()

    for definition in discover(paths, max_depth=max_depth):
        base_version = definition.version.base_version
        mapping.setdefault(definition.identifier, {})
        mapping[definition.identifier][base_version] = definition

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
    """Get best matching :class:`Definition` instance for *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier.

    :exc:`packaging.requirements.InvalidRequirement` is raised if the
    requirement specifier is incorrect.

    """
    if requirement.name not in definition_mapping:
        raise RuntimeError(
            "The requirement '{}' could not be resolved."
            .format(requirement.name)
        )

    definition = None

    # Sort the definition so that the highest version is first. It is more
    # efficient to do the sorting when a definition is required rather than for
    # all the definitions found in the registries...
    sorted_definitions = sorted(
        definition_mapping[requirement.name].values(),
        key=lambda _definition: _definition.version,
        reverse=True
    )

    # Get the best matching definition.
    for definition in sorted_definitions:
        if definition.version in requirement.specifier:
            definition = definition
            break

    if definition is None:
        raise RuntimeError(
            "The requirement '{}' could not be resolved."
            .format(requirement.name)
        )

    if len(requirement.extras) > 0:
        variant = next(iter(requirement.extras))
        variant_mapping = definition.get("variant", {})

        if variant not in variant_mapping.keys():
            raise RuntimeError(
                "The variant '{}' could not been resolved for '{}'.".format(
                    variant, requirement.name
                )
            )

        # Merge variant environment with the global environment if necessary.
        definition["environ"] = umwelt.environment.merge_environments(
            definition, variant_mapping[variant]
        )

        # Update the definition requirement if necessary.
        definition_requirement = (
            definition.get("requirement", []) +
            variant_mapping[variant].get("requirement", [])
        )

        if len(definition_requirement) > 0:
            definition["requirement"] = definition_requirement

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

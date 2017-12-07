# :coding: utf-8

import os
import collections
import json

from packaging.requirements import Requirement
from packaging.version import Version
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


def search_definitions(definition_specifier, paths, max_depth=None):
    """Return mapping from environment definitions matching *requirement*.

    *definition_specifier* can indicate a definition specifier which must
    adhere to `PEP 508 <https://www.python.org/dev/peps/pep-0508>`_.

    :exc:`packaging.requirements.InvalidRequirement` is raised if the
    requirement specifier is incorrect.

    :func:`~umwelt.definition.discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".search_definitions")
    logger.info(
        "Search environment definition definitions matching {0!r}"
        .format(definition_specifier)
    )

    mapping = dict()

    for definition in discover(paths, max_depth=max_depth):
        requirement = Requirement(definition_specifier)
        if (
            requirement.name in definition.identifier or
            requirement.name in definition.description
        ):
            if Version(definition.version) in requirement.specifier:
                mapping.setdefault(definition.identifier, [])
                mapping[definition.identifier].append(definition)

    return mapping


def get(definition_specifier, definition_mapping):
    """Get fittest :class:`Definition` instance for *definition_specifier*.

    *definition_specifier* can indicate a definition specifier which must
    adhere to `PEP 508 <https://www.python.org/dev/peps/pep-0508>`_.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier.

    :exc:`packaging.requirements.InvalidRequirement` is raised if the
    requirement specifier is incorrect.

    """
    requirement = Requirement(definition_specifier)
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
        if Version(definition.version) in requirement.specifier:
            required_definition = definition
            break

    if required_definition is None:
        raise RuntimeError(
            "No definition has been found for this specifier: {!r}."
            .format(definition_specifier)
        )

    return required_definition


def resolve_dependencies(definition, definition_mapping):
    """Return *definition* augmented with its dependency definitions.

    Look for dependencies keyword in *definition* and replace all specifier by
    the corresponding definition.

    """
    logger = mlog.Logger(__name__ + ".discover")
    logger.debug(
        "Resolve dependencies for {} [{}]."
        .format(definition.identifier, definition.version)
    )

    dependencies = definition.get("dependency", [])
    logger.debug("Dependencies: {!r}".format(dependencies))

    # Reset the dependency array before filling it with definition instances
    definition["dependency"] = []

    for definition_specifier in dependencies:
        dependent_definition = get(definition_specifier, definition_mapping)
        definition["dependency"].append(dependent_definition)

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
                except (IOError, ValueError, TypeError):
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
    """Load and return :class:`Environment` from *path*."""
    with open(path, "r") as stream:
        environment_data = json.load(stream)
        # TODO: Validate with JSON-Schema.
        environment = Definition(**environment_data)
        return environment


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

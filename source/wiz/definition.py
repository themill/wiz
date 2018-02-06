# :coding: utf-8

import os
import json
import collections

import mlog
from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import Version, InvalidVersion

import wiz.symbol
import wiz.exception
import wiz.filesystem


def fetch(paths, max_depth=None):
    """Return mapping from all definitions available under *paths*.

    :func:`discover` available definitions under *paths*, searching recursively
    up to *max_depth*.

    """
    mapping = {
        wiz.symbol.APPLICATION_TYPE: {},
        wiz.symbol.ENVIRONMENT_TYPE: {}
    }

    for definition in discover(paths, max_depth=max_depth):
        if definition.type == wiz.symbol.ENVIRONMENT_TYPE:
            mapping[definition.type].setdefault(definition.identifier, [])
            mapping[definition.type][definition.identifier].append(definition)
        elif definition.type == wiz.symbol.APPLICATION_TYPE:
            mapping[definition.type][definition.identifier] = definition

    return mapping


def search(requirements, paths, max_depth=None):
    """Return mapping from definitions matching *requirement*.

    *requirement* should be an instance of
    :class:`packaging.requirements.Requirement`.

    :func:`~wiz.definition.discover` available definitions under *paths*,
    searching recursively up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".search")
    logger.info(
        "Search definitions matching '{}'".format(
            ", ".join(map(str, requirements))
        )
    )

    mapping = {
        wiz.symbol.APPLICATION_TYPE: {},
        wiz.symbol.ENVIRONMENT_TYPE: {}
    }

    for definition in discover(paths, max_depth=max_depth):
        compatible = True

        for requirement in requirements:
            if not (
                requirement.name.lower() in definition.identifier.lower() or
                requirement.name.lower() in definition.description.lower()
            ):
                compatible = False
                break

            if (
                definition.type == wiz.symbol.ENVIRONMENT_TYPE and
                definition.version not in requirement.specifier
            ):
                compatible = False
                break

        if not compatible:
            continue

        if definition.type == wiz.symbol.ENVIRONMENT_TYPE:
            mapping[definition.type].setdefault(definition.identifier, [])
            mapping[definition.type][definition.identifier].append(definition)

        elif definition.type == wiz.symbol.APPLICATION_TYPE:
            mapping[definition.type][definition.identifier] = definition

    return mapping


def discover(paths, max_depth=None):
    """Discover and yield all definitions found under *paths*.

    If *max_depth* is None, search all sub-trees under each path for
    definition files in JSON format. Otherwise, only search up to *max_depth*
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
        logger.debug("Searching under {!r} for definition files.".format(path))

        initial_depth = path.rstrip(os.sep).count(os.sep)
        for base, _, filenames in os.walk(path):
            depth = base.count(os.sep)
            if max_depth is not None and (depth - initial_depth) > max_depth:
                continue

            for filename in filenames:
                _, extension = os.path.splitext(filename)
                if extension != ".json":
                    continue

                definition_path = os.path.join(base, filename)
                logger.debug(
                    "Discovered definition file {!r}.".format(definition_path)
                )

                try:
                    definition = load(definition_path)
                    definition["registry"] = path

                    if definition.get("disabled", False):
                        logger.warning(
                            "Definition fetched from {!r} is"
                            " disabled".format(definition_path),
                        )
                        continue

                except (
                    IOError, ValueError, TypeError,
                    wiz.exception.WizError
                ):
                    logger.warning(
                        "Error occurred trying to load definition "
                        "from {!r}".format(definition_path),
                        traceback=True
                    )
                    continue
                else:
                    logger.debug(
                        "Loaded definition {!r} from {!r}."
                        .format(definition.identifier, definition_path)
                    )
                    yield definition


def load(path):
    """Load and return a definition from *path*.

    If the definition data is of type "environment", an :class:`Environment`
    instance will be returned.

    If the definition data is of type "application", an :class:`Application`
    instance will be returned.

    A :exc:`wiz.exception.IncorrectDefinition` exception will be raised
    otherwise.

    """
    with open(path, "r") as stream:
        definition_data = json.load(stream)
        return create(definition_data)


def create(definition_data):
    """Return definition from *definition_data*.

    If the definition data is of type "environment", an :class:`Environment`
    instance will be returned.

    If the definition data is of type "application", an :class:`Application`
    instance will be returned.

    A :exc:`wiz.exception.IncorrectDefinition` exception will be raised
    otherwise.

    """
    # TODO: Validate with JSON-Schema.

    if definition_data.get("type") == wiz.symbol.ENVIRONMENT_TYPE:
        definition = Environment(**definition_data)
        return definition

    elif definition_data.get("type") == wiz.symbol.APPLICATION_TYPE:
        definition = Application(**definition_data)
        return definition

    raise wiz.exception.IncorrectDefinition(
        "The definition type is incorrect: {}".format(
            definition_data.get("type")
        )
    )


class _Definition(collections.MutableMapping):
    """Base Definition object."""

    def __init__(self, *args, **kwargs):
        """Initialise definition."""
        super(_Definition, self).__init__()
        self._mapping = {}
        self.update(*args, **kwargs)

    def _validate(self):
        """Validate the definition."""
        raise NotImplemented

    @property
    def type(self):
        """Return application type."""
        raise NotImplemented

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    def sorted_mapping(self):
        """Return ordered definition data."""
        raise NotImplemented

    def encode(self):
        """Return serialized definition data."""
        return json.dumps(
            self.sorted_mapping(),
            indent=4,
            separators=(",", ": "),
            ensure_ascii=False
        )

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


class Environment(_Definition):
    """Environment Definition."""

    def __init__(self, *args, **kwargs):
        """Initialise environment definition."""
        super(Environment, self).__init__(*args, **kwargs)
        self._validate()

    def _validate(self):
        """Validate the definition."""
        try:
            self._mapping["version"] = Version(self.version)
            self._mapping["requirement"] = map(
                Requirement, self.get("requirement", [])
            )

            for variant_mapping in self._mapping.get("variant", []):
                variant_mapping["requirement"] = map(
                    Requirement, variant_mapping.get("requirement", [])
                )

        except (InvalidRequirement, InvalidVersion) as error:
            raise wiz.exception.IncorrectEnvironment(
                "The environment '{}' is incorrect: {}".format(
                    self.identifier, error
                )
            )

    @property
    def type(self):
        """Return environment type."""
        return wiz.symbol.ENVIRONMENT_TYPE

    @property
    def version(self):
        """Return version."""
        return self.get("version", "unknown")

    def sorted_mapping(self):
        """Return ordered definition data."""
        mapping = self._mapping.copy()

        content = collections.OrderedDict()

        content["identifier"] = mapping.pop("identifier")
        content["version"] = str(mapping.pop("version"))
        content["type"] = mapping.pop("type")
        content["description"] = mapping.pop("description", "unknown")

        if len(mapping.get("system", {})) > 0:
            content["system"] = mapping.pop("system")

        if len(mapping.get("command", {})) > 0:
            content["command"] = mapping.pop("command")

        if len(mapping.get("data", {})) > 0:
            content["data"] = mapping.pop("data")

        if len(mapping.get("requirement", [])) > 0:
            content["requirement"] = map(str, mapping.pop("requirement"))

        if len(mapping.get("variant", [])) > 0:
            variants = []

            for variant in mapping.pop("variant", []):
                _content = collections.OrderedDict()
                _content["identifier"] = variant.get("identifier")

                if len(variant.get("data", {})) > 0:
                    _content["data"] = variant.get("data")

                if len(variant.get("requirement", [])) > 0:
                    _content["requirement"] = map(
                        str, variant.get("requirement")
                    )

                _content.update(variant)
                variants.append(_content)

            content["variant"] = variants

        content.update(mapping)
        return content


class Application(_Definition):
    """Application Definition."""

    def __init__(self, *args, **kwargs):
        """Initialise application definition."""
        super(Application, self).__init__(*args, **kwargs)
        self._validate()

    def _validate(self):
        """Validate the definition."""
        try:
            self._mapping["requirement"] = map(
                Requirement, self.get("requirement", [])
            )

        except InvalidRequirement as error:
            raise wiz.exception.IncorrectApplication(
                "The application '{}' is incorrect: {}".format(
                    self.identifier, error
                )
            )

    @property
    def type(self):
        """Return application type."""
        return wiz.symbol.APPLICATION_TYPE

    @property
    def command(self):
        """Return command."""
        return self.get("command")

    @property
    def requirement(self):
        """Return requirement list."""
        return self.get("requirement", [])

    def sorted_mapping(self):
        """Return ordered definition data."""
        mapping = self._mapping.copy()

        content = collections.OrderedDict()

        content["identifier"] = mapping.pop("identifier")
        content["type"] = mapping.pop("type")
        content["description"] = mapping.pop("description", "unknown")
        content["command"] = mapping.pop("command")
        content["requirement"] = map(str, mapping.pop("requirement"))

        content.update(mapping)
        return content

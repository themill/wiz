# :coding: utf-8

import os
import json
import collections
import abc

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
        identifier = definition.identifier

        if definition.type == wiz.symbol.ENVIRONMENT_TYPE:
            version = definition.version.base_version
            mapping[definition.type].setdefault(identifier, {})
            mapping[definition.type][identifier][version] = definition

        elif definition.type == wiz.symbol.APPLICATION_TYPE:
            mapping[definition.type][identifier] = definition

    return mapping


def search(requests, paths, max_depth=None):
    """Return mapping from definitions matching *requirement*.

    *requests* should be a list of element which can influence the definition
    research. It can be in the form of "app-env >= 1.0.0, < 2" in order to
    affine the research to a particular version range.

    :func:`~wiz.definition.discover` available definitions under *paths*,
    searching recursively up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".search")
    logger.info("Search definitions matching '{}'".format(" ".join(requests)))

    mapping = {
        wiz.symbol.APPLICATION_TYPE: {},
        wiz.symbol.ENVIRONMENT_TYPE: {}
    }

    requirements = []
    for request in requests:
        try:
            requirement = Requirement(request)
        except InvalidRequirement:
            continue

        requirements.append(requirement)

    if len(requirements) == 0:
        return mapping

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

        identifier = definition.identifier

        if definition.type == wiz.symbol.ENVIRONMENT_TYPE:
            version = definition.version.base_version
            mapping[definition.type].setdefault(definition.identifier, {})
            mapping[definition.type][identifier][version] = definition

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
                    definition = load(
                        definition_path, mapping={"registry": path}
                    )

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


def load(path, mapping=None):
    """Load and return a definition from *path*.

    *mapping* can indicate a optional mapping which will augment the data
    leading to the creation of the definition.

    If the definition data is of type "environment", an :class:`Environment`
    instance will be returned.

    If the definition data is of type "application", an :class:`Application`
    instance will be returned.

    A :exc:`wiz.exception.IncorrectDefinition` exception will be raised
    otherwise.

    """
    if mapping is None:
        mapping = {}

    with open(path, "r") as stream:
        definition_data = json.load(stream)
        definition_data.update(mapping)
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


class _Definition(collections.Mapping):
    """Base Definition object."""

    def __init__(self, *args, **kwargs):
        """Initialise definition."""
        self._mapping = dict(*args, **kwargs)

    @property
    def type(self):
        """Return application type."""
        return self.get("type")

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    def to_mapping(self):
        """Return ordered definition data."""
        return self._mapping.copy()

    @abc.abstractmethod
    def to_ordered_mapping(self):
        """Return ordered definition data."""

    def encode(self):
        """Return serialized definition data."""
        return json.dumps(
            self.to_ordered_mapping(),
            indent=4,
            separators=(",", ": "),
            ensure_ascii=False
        )

    def __getitem__(self, key):
        """Return value for *key*."""
        return self._mapping[key]

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
        mapping = dict(*args, **kwargs)
        mapping["type"] = wiz.symbol.ENVIRONMENT_TYPE

        try:
            self._version = None
            if "version" in mapping.keys():
                self._version = Version(mapping["version"])

            self._requirement = map(Requirement, mapping.get("requirement", []))
            self._variant = map(
                lambda variant: _EnvironmentVariant(
                    variant, mapping.get("identifier")
                ),
                mapping.get("variant", [])
            )

        except (InvalidRequirement, InvalidVersion) as exception:
            raise wiz.exception.IncorrectEnvironment(
                "The environment '{}' is incorrect: {}".format(
                    mapping.get("identifier"), exception
                )
            )

        super(Environment, self).__init__(mapping)

    def __str__(self):
        """Return string representation."""
        return "'{identifier}' [{version}]".format(
            identifier=self.identifier, version=self.version
        )

    @property
    def version(self):
        """Return version."""
        return self._version or "unknown"

    @property
    def data(self):
        """Return data mapping."""
        return self.get("data", {})

    @property
    def alias(self):
        """Return alias mapping."""
        return self.get("alias", {})

    @property
    def system(self):
        """Return system constraint mapping."""
        return self.get("system", {})

    @property
    def requirement(self):
        """Return requirement list."""
        return self._requirement

    @property
    def variant(self):
        """Return requirement list."""
        return self._variant

    def to_ordered_mapping(self):
        """Return ordered definition data."""
        mapping = self.to_mapping()

        content = collections.OrderedDict()
        content["identifier"] = mapping.pop("identifier")

        if mapping.get("version") is not None:
            content["version"] = mapping.pop("version")

        content["type"] = mapping.pop("type")

        if mapping.get("description") is not None:
            content["description"] = mapping.pop("description")

        if len(mapping.get("system", {})) > 0:
            content["system"] = mapping.pop("system")

        if len(mapping.get("alias", {})) > 0:
            content["alias"] = mapping.pop("alias")

        if len(mapping.get("data", {})) > 0:
            content["data"] = mapping.pop("data")

        if len(mapping.get("requirement", [])) > 0:
            content["requirement"] = mapping.pop("requirement")

        if len(mapping.get("variant", [])) > 0:
            content["variant"] = [
                variant.to_ordered_mapping() for variant
                in self.variant
            ]
            mapping.pop("variant")

        content.update(mapping)
        return content


class _EnvironmentVariant(_Definition):
    """Environment Variant Definition."""

    def __init__(self, variant, identifier):
        """Initialise environment variant definition."""
        mapping = dict(variant)
        self._identifier = identifier
        self._requirement = map(Requirement, mapping.get("requirement", []))
        super(_EnvironmentVariant, self).__init__(mapping)

    def __str__(self):
        """Return string representation."""
        return "'{identifier}' [{variant_name}]".format(
            identifier=self._identifier, variant_name=self.identifier
        )

    @property
    def alias(self):
        """Return alias mapping."""
        return self.get("alias", {})

    @property
    def data(self):
        """Return data mapping."""
        return self.get("data", {})

    @property
    def requirement(self):
        """Return requirement list."""
        return self._requirement

    def to_ordered_mapping(self):
        """Return ordered definition data."""
        mapping = self.to_mapping()

        content = collections.OrderedDict()
        content["identifier"] = mapping.pop("identifier")

        if len(mapping.get("alias", {})) > 0:
            content["alias"] = mapping.pop("alias")

        if len(mapping.get("data", {})) > 0:
            content["data"] = mapping.pop("data")

        if len(mapping.get("requirement", [])) > 0:
            content["requirement"] = mapping.pop("requirement")

        content.update(mapping)
        return content


class Application(_Definition):
    """Application Definition."""

    def __init__(self, *args, **kwargs):
        """Initialise application definition."""
        mapping = dict(*args, **kwargs)
        mapping["type"] = wiz.symbol.APPLICATION_TYPE

        try:
            self._requirement = map(Requirement, mapping.get("requirement", []))

        except InvalidRequirement as error:
            raise wiz.exception.IncorrectApplication(
                "The application '{}' is incorrect: {}".format(
                    mapping.get("identifier"), error
                )
            )

        super(Application, self).__init__(mapping)

    def __str__(self):
        """Return string representation."""
        return "'{identifier}'".format(identifier=self.identifier)

    @property
    def command(self):
        """Return command."""
        return self.get("command")

    @property
    def requirement(self):
        """Return requirement list."""
        return self._requirement

    def to_ordered_mapping(self):
        """Return ordered definition data."""
        mapping = self.to_mapping()

        content = collections.OrderedDict()
        content["identifier"] = mapping.pop("identifier")
        content["type"] = mapping.pop("type")

        if mapping.get("description") is not None:
            content["description"] = mapping.pop("description")

        content["command"] = mapping.pop("command")
        content["requirement"] = mapping.pop("requirement")

        content.update(mapping)
        return content

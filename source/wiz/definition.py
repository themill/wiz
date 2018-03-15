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


def fetch(paths, requests=None, max_depth=None):
    """Return mapping from all definitions available under *paths*.

    *requests* could be a list of element which can influence the definition
    research. It can be in the form of "app-env >= 1.0.0, < 2" in order to
    affine the research to a particular version range.

    :func:`discover` available definitions under *paths*, searching recursively
    up to *max_depth*.

    """
    mapping = {
        wiz.symbol.PACKAGE_REQUEST_TYPE: {},
        wiz.symbol.COMMAND_REQUEST_TYPE: {}
    }

    for definition in discover(paths, max_depth=max_depth):
        if requests is not None and not validate(definition, requests):
            continue

        identifier = definition.identifier
        version = str(definition.version)

        # Record package definition.
        package_type = wiz.symbol.PACKAGE_REQUEST_TYPE
        command_type = wiz.symbol.PACKAGE_REQUEST_TYPE

        mapping[package_type].setdefault(identifier, {})
        mapping[package_type][identifier][version] = definition

        # Record commands from definition.
        for command in definition.command.keys():
            mapping[command_type][command] = definition.identifier

    return mapping


def validate(definition, requests):
    """Indicate whether *definition* is compatible with *requests*.

    *definition* should be a :class:`Definition` instance.

    *requests* could be a list of element which can influence the definition
    research. It can be in the form of "app-env >= 1.0.0, < 2" in order to
    affine the research to a particular version range.

    """
    requirements = []

    # Convert requests into requirements.
    for request in requests:
        try:
            requirement = Requirement(request)
        except InvalidRequirement:
            continue

        requirements.append(requirement)

    if len(requirements) == 0:
        return False

    # Ensure that each requirement is compatible with definition.
    compatible = True

    for requirement in requirements:
        if not (
            requirement.name.lower() in definition.identifier.lower() or
            requirement.name.lower() in definition.description.lower()
        ):
            compatible = False
            break

        if definition.version not in requirement.specifier:
            compatible = False
            break

    return compatible


def get(requirement, definition_mapping):
    """Get best matching definition version from *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available definition
    associated with their unique identifier.

    :exc:`wiz.exception.RequestNotFound` is raised if the requirement can not
    be resolved.

    """
    if requirement.name not in definition_mapping:
        raise wiz.exception.RequestNotFound(requirement)

    definition = None

    # Sort the definition versions so that the highest one is first.
    versions = sorted(
        map(lambda d: d.version, definition_mapping[requirement.name].values()),
        reverse=True
    )

    # Get the best matching definition.
    for version in versions:
        _definition = definition_mapping[requirement.name][str(version)]
        if _definition.version in requirement.specifier:
            definition = _definition
            break

    if definition is None:
        raise wiz.exception.RequestNotFound(requirement)

    return definition


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

    A :exc:`wiz.exception.IncorrectDefinition` exception will be raised
    otherwise.

    """
    if mapping is None:
        mapping = {}

    with open(path, "r") as stream:
        definition_data = json.load(stream)
        definition_data.update(mapping)
        return Definition(**definition_data)


class _DefinitionBase(collections.Mapping):
    """Base Definition object."""

    def __init__(self, *args, **kwargs):
        """Initialise base definition."""
        self._mapping = dict(*args, **kwargs)

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


class Definition(_DefinitionBase):
    """Definition object."""

    def __init__(self, *args, **kwargs):
        """Initialise definition."""
        mapping = dict(*args, **kwargs)

        try:
            self._version = None
            if "version" in mapping.keys():
                self._version = Version(mapping["version"])

            requirements = mapping.get("requirements", [])
            self._requirements = map(Requirement, requirements)

        except InvalidVersion:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' has an incorrect "
                "version [{version}]".format(
                    identifier=mapping.get("identifier"),
                    version=mapping["version"]
                )
            )

        except InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' contains an incorrect "
                "requirement [{error}]".format(
                    identifier=mapping.get("identifier"),
                    error=exception
                )
            )

        super(Definition, self).__init__(mapping)

        variants = mapping.get("variants", [])
        self._variants = map(
            lambda variant: _Variant(variant, self), variants
        )

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def version(self):
        """Return version."""
        return self._version or "unknown"

    @property
    def description(self):
        """Return description."""
        return self.get("description", "unknown")

    @property
    def environ(self):
        """Return environ mapping."""
        return self.get("environ", {})

    @property
    def command(self):
        """Return command mapping."""
        return self.get("command", {})

    @property
    def system(self):
        """Return system constraint mapping."""
        return self.get("system", {})

    @property
    def requirements(self):
        """Return requirement list."""
        return self._requirements

    @property
    def variants(self):
        """Return variant list."""
        return self._variants

    def to_ordered_mapping(self):
        """Return ordered definition data."""
        mapping = self.to_mapping()

        content = collections.OrderedDict()
        content["identifier"] = mapping.pop("identifier")

        if mapping.get("version") is not None:
            content["version"] = mapping.pop("version")

        if mapping.get("description") is not None:
            content["description"] = mapping.pop("description")

        if len(mapping.get("system", {})) > 0:
            content["system"] = mapping.pop("system")

        if len(mapping.get("command", {})) > 0:
            content["command"] = mapping.pop("command")

        if len(mapping.get("environ", {})) > 0:
            content["environ"] = mapping.pop("environ")

        if len(mapping.get("requirements", [])) > 0:
            content["requirements"] = mapping.pop("requirements")

        if len(mapping.get("variants", [])) > 0:
            content["variants"] = [
                variant.to_ordered_mapping() for variant in self.variants
            ]
            mapping.pop("variants")

        content.update(mapping)
        return content


class _Variant(_DefinitionBase):
    """Environment Variant Definition."""

    def __init__(self, variant, definition):
        """Initialise variant definition."""
        mapping = dict(variant)
        self._definition = definition

        try:
            requirements = mapping.get("requirements", [])
            self._requirements = map(Requirement, requirements)

        except InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' [{variant}] contains an "
                "incorrect requirement [{error}]".format(
                    identifier=definition.identifier,
                    variant=mapping.get("identifier"),
                    error=exception
                )
            )

        self._requirements = map(Requirement, mapping.get("requirements", []))
        super(_Variant, self).__init__(mapping)

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def definition(self):
        """Return corresponding definition."""
        return self._definition

    @property
    def environ(self):
        """Return environ mapping."""
        return self.get("environ", {})

    @property
    def command(self):
        """Return command mapping."""
        return self.get("command", {})

    @property
    def requirements(self):
        """Return requirement list."""
        return self._requirements

    def to_ordered_mapping(self):
        """Return ordered definition data."""
        mapping = self.to_mapping()

        content = collections.OrderedDict()
        content["identifier"] = mapping.pop("identifier")

        if len(mapping.get("command", {})) > 0:
            content["command"] = mapping.pop("command")

        if len(mapping.get("environ", {})) > 0:
            content["environ"] = mapping.pop("environ")

        if len(mapping.get("requirements", [])) > 0:
            content["requirements"] = mapping.pop("requirements")

        content.update(mapping)
        return content

# :coding: utf-8

import os
import json

import mlog

import wiz.symbol
import wiz.mapping
import wiz.package
import wiz.filesystem
import wiz.exception
import wiz.system
import wiz.history
import wiz.utility
import wiz.validator


def fetch(paths, requests=None, system_mapping=None, max_depth=None):
    """Return mapping from all definitions available under *paths*.

    A definition mapping should be in the form of::

        {
            "command": {
                "app": "my-app",
                ...
            },
            "package": {
                "my-app": {
                    "1.1.0": <Definition(identifier="my-app", version="1.1.0")>,
                    "1.0.0": <Definition(identifier="my-app", version="1.0.0")>,
                    "0.1.0": <Definition(identifier="my-app", version="0.1.0")>,
                    ...
                },
                ...
            },
            "implicit-packages": [
                "foo==0.1.0", ...
            ]
        }

    *requests* could be a list of element which can influence the definition
    research. It can be in the form of "package >= 1.0.0, < 2" in order to
    affine the research to a particular version range.

    *system_mapping* could be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    :func:`discover` available definitions under *paths*, searching recursively
    up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".fetch")

    mapping = {
        wiz.symbol.PACKAGE_REQUEST_TYPE: {},
        wiz.symbol.COMMAND_REQUEST_TYPE: {},
        wiz.symbol.IMPLICIT_PACKAGE: []
    }

    # Record definitions which should be implicitly used.
    implicit_definitions = []
    implicit_definition_mapping = {}

    for definition in discover(paths, max_depth=max_depth):
        if requests is not None and not validate(definition, requests):
            continue

        if (
            system_mapping is not None and
            not wiz.system.validate(definition, system_mapping)
        ):
            continue

        identifier = definition.identifier
        version = str(definition.version)

        # Record package definition.
        package_type = wiz.symbol.PACKAGE_REQUEST_TYPE
        command_type = wiz.symbol.COMMAND_REQUEST_TYPE

        mapping[package_type].setdefault(identifier, {})
        mapping[package_type][identifier][version] = definition

        # Record package identifiers which should be used implicitly in context.
        if definition.get("auto-use"):
            implicit_definitions.append(identifier)
            implicit_definition_mapping.setdefault(identifier, {})
            implicit_definition_mapping[identifier][version] = definition
            logger.debug(
                "Definition '{}=={}' set to be implicitly used with 'auto-use' "
                "keyword".format(identifier, version)
            )

        # Record commands from definition.
        for command in definition.command.keys():
            mapping[command_type][command] = definition.identifier

    # Add implicit package identifiers of best matching definitions which have
    # the 'auto-use' keyword in inverse order of discovery to give priority
    # to the latest discovered.
    for definition_identifier in sorted(
        implicit_definition_mapping.keys(),
        key=lambda _id: implicit_definitions.index(_id),
        reverse=True
    ):
        requirement = wiz.utility.get_requirement(definition_identifier)
        definition = query(requirement, implicit_definition_mapping)
        mapping[wiz.symbol.IMPLICIT_PACKAGE].append(
            wiz.package.generate_identifier(definition)
        )

    wiz.history.record_action(
        wiz.symbol.DEFINITIONS_COLLECTION_ACTION,
        registries=paths, max_depth=max_depth, definition_mapping=mapping
    )

    return mapping


def validate(definition, requests):
    """Indicate whether *definition* is compatible with *requests*.

    *definition* should be a :class:`Definition` instance.

    *requests* could be a list of element which can influence the definition
    research. It can be in the form of "package >= 1.0.0, < 2" in order to
    affine the research to a particular version range.

    """
    # Convert requests into requirements.
    requirements = [
        wiz.utility.get_requirement(request) for request in requests
    ]
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


def query(requirement, definition_mapping):
    """Return best matching definition version from *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available definition
    associated with their unique identifier.

    :exc:`wiz.exception.RequestNotFound` is raised if the requirement can not
    be resolved.

    """
    identifier = requirement.name
    if identifier not in definition_mapping:
        raise wiz.exception.RequestNotFound(requirement)

    definition = None

    # Sort the definition versions so that the highest one is first.
    versions = sorted(
        map(lambda d: d.version, definition_mapping[identifier].values()),
        reverse=True
    )

    if wiz.symbol.UNKNOWN_VALUE in versions and len(versions) > 1:
        raise wiz.exception.RequestNotFound(
            "Impossible to retrieve the best matching definition for "
            "'{}' as non-versioned and versioned definitions have "
            "been fetched.".format(identifier)
        )

    # Get the best matching definition.
    for version in versions:
        _definition = definition_mapping[identifier][str(version)]
        if _definition.version in requirement.specifier:
            definition = _definition
            break

    if definition is None:
        raise wiz.exception.RequestNotFound(requirement)

    return definition


def export(path, definition, overwrite=False):
    """Export *definition* as a :term:`JSON` file to *path*.

    Return exported definition file path.

    *path* should be a valid directory to save the exported definition.

    *definition* could be an instance of :class:`Definition` or a mapping in
    the form of::

        {
            "identifier": "my-package",
            "description": "This is my package",
            "version": "0.1.0",
            "command": {
                "app": "AppExe",
                "appX": "AppExe --mode X"
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2"
            },
            "requirements": [
                "package1 >=1, <2",
                "package2"
            ]
        }

    The identifier must be unique in the registry so that it could be
    :func:`queried <query>`.

    *overwrite* indicate whether existing definitions in the target path
    will be overwritten. Default is False.

    Raises :exc:`wiz.exception.IncorrectDefinition` if *data* is a mapping that
    cannot create a valid instance of :class:`wiz.definition.Definition`.

    Raises :exc:`wiz.exception.FileExists` if definition already exists in
    *path* and overwrite is False.

    Raises :exc:`OSError` if the definition can not be exported in *path*.

    The command identifier must also be unique in the registry.

    """
    if not isinstance(definition, Definition):
        definition = wiz.definition.Definition(**definition)

    file_name = wiz.utility.compute_file_name(definition)
    file_path = os.path.join(os.path.abspath(path), file_name)
    wiz.filesystem.export(file_path, definition.encode(), overwrite=overwrite)
    return file_path


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
                        definition_path, mapping={
                            "registry": path,
                            "definition-location": definition_path,
                        }
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
    if the definition is incorrect.

    """
    if mapping is None:
        mapping = {}

    with open(path, "r") as stream:
        definition_data = json.load(stream)
        definition_data.update(mapping)
        return Definition(**definition_data)


class Definition(wiz.mapping.Mapping):
    """Definition object."""

    def __init__(self, *args, **kwargs):
        """Initialise definition."""
        mapping = dict(*args, **kwargs)

        for error in wiz.validator.yield_definition_errors(mapping):
            # Ensure that message can be used within format string syntax
            message = error.get("message").replace("{", "{{").replace("}", "}}")
            raise wiz.exception.IncorrectDefinition(
                "{message} ({path})".format(
                    message=message,
                    path=error.get("path"),
                )
            )

        try:
            if "version" in mapping.keys():
                mapping["version"] = wiz.utility.get_version(mapping["version"])

        except wiz.exception.InvalidVersion:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' has an incorrect "
                "version [{version}]".format(
                    identifier=mapping.get("identifier"),
                    version=mapping["version"]
                )
            )

        try:
            if "requirements" in mapping.keys():
                mapping["requirements"] = [
                    wiz.utility.get_requirement(requirement)
                    for requirement in mapping["requirements"]
                ]

        except wiz.exception.InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' contains an incorrect "
                "package requirement [{error}]".format(
                    identifier=mapping.get("identifier"),
                    error=exception
                )
            )

        try:
            if "constraints" in mapping.keys():
                mapping["constraints"] = [
                    wiz.utility.get_requirement(requirement)
                    for requirement in mapping["constraints"]
                ]

        except wiz.exception.InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' contains an incorrect "
                "package constraint [{error}]".format(
                    identifier=mapping.get("identifier"),
                    error=exception
                )
            )

        if "variants" in mapping.keys():
            mapping["variants"] = [
                _Variant(
                    dict(definition=mapping.get("identifier"), **variant)
                ) for variant in mapping["variants"]
            ]

        super(Definition, self).__init__(mapping)

    def set(self, element, value):
        """Returns copy of instance with *element* set to *value*.
        """
        _mapping = self.to_dict(serialize_content=True)
        _mapping[element] = value
        return self.__class__(**_mapping)

    def sanitized(self):
        """Return definition instance without keywords added by API."""
        _definition = self.remove("definition-location")
        _definition = _definition.remove("registry")
        return _definition

    def update(self, element, value):
        """Returns copy of instance with *element* mapping updated with *value*.

        Raise :exc:`ValueError` if *element* is not a dictionary.

        """
        _mapping = self.to_dict(serialize_content=True)
        _mapping.setdefault(element, {})

        if not isinstance(_mapping[element], dict):
            raise ValueError(
                "Impossible to update '{}' as it is not a "
                "dictionary.".format(element)
            )

        _mapping[element].update(value)
        return self.__class__(**_mapping)

    def extend(self, element, values):
        """Returns copy of instance with *element* list extended with *values*.

        Raise :exc:`ValueError` if *mapping* is not a list.

        """
        _mapping = self.to_dict(serialize_content=True)
        _mapping.setdefault(element, [])

        if not isinstance(_mapping[element], list):
            raise ValueError(
                "Impossible to extend '{}' as it is not a list.".format(element)
            )

        _mapping[element].extend(values)
        return self.__class__(**_mapping)

    def insert(self, element, value, index):
        """Returns copy of instance with *value* inserted in *element* list.

        *index* should be the index number at which the *value* should be
        inserted.

        Raise :exc:`ValueError` if *mapping* is not a list.

        """
        _mapping = self.to_dict(serialize_content=True)
        _mapping.setdefault(element, [])

        if not isinstance(_mapping[element], list):
            raise ValueError(
                "Impossible to insert '{}' in '{}' as it is not "
                "a list.".format(value, element)
            )

        _mapping[element].insert(index, value)
        return self.__class__(**_mapping)

    def remove(self, element):
        """Returns copy of instance without *element*."""
        _mapping = self.to_dict(serialize_content=True)
        if element not in _mapping.keys():
            return self

        del _mapping[element]
        return self.__class__(**_mapping)

    def remove_key(self, element, value):
        """Returns copy of instance without key *value* from *element* mapping.

        If *element* mapping is empty after removing *value*, the *element* key
        will be removed.

        Raise :exc:`ValueError` if *element* is not a dictionary.

        """
        _mapping = self.to_dict(serialize_content=True)
        if element not in _mapping.keys():
            return self

        if not isinstance(_mapping[element], dict):
            raise ValueError(
                "Impossible to remove key from '{}' as it is not a "
                "dictionary.".format(element)
            )

        if value not in _mapping[element].keys():
            return self

        del _mapping[element][value]
        if len(_mapping[element]) == 0:
            del _mapping[element]

        return self.__class__(**_mapping)

    def remove_index(self, element, index):
        """Returns copy of instance without *index* from *element* list.

        If *element* list is empty after removing *index*, the *element* key
        will be removed.

        Raise :exc:`ValueError` if *element* is not a list.

        """
        _mapping = self.to_dict(serialize_content=True)
        if element not in _mapping.keys():
            return self

        if not isinstance(_mapping[element], list):
            raise ValueError(
                "Impossible to remove index from '{}' as it is not a "
                "list.".format(element)
            )

        if index >= len(_mapping[element]):
            return self

        del _mapping[element][index]
        if len(_mapping[element]) == 0:
            del _mapping[element]

        return self.__class__(**_mapping)

    @property
    def variants(self):
        """Return variant list."""
        return self.get("variants", [])

    @property
    def _ordered_keywords(self):
        """Return ordered keywords."""
        return [
            "identifier",
            "version",
            "description",
            "registry",
            "definition-location",
            "install-location",
            'group',
            "auto-use",
            "system",
            "command",
            "environ",
            "requirements",
            "constraints",
            "variants"
        ]


class _Variant(wiz.mapping.Mapping):
    """Variant Definition object."""

    def __init__(self, *args, **kwargs):
        """Initialise variant definition."""
        mapping = dict(*args, **kwargs)
        self.definition_identifier = mapping.pop("definition")

        try:
            if "requirements" in mapping.keys():
                mapping["requirements"] = [
                    wiz.utility.get_requirement(requirement)
                    for requirement in mapping["requirements"]
                ]

        except wiz.exception.InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' [{variant}] contains an "
                "incorrect package requirement [{error}]".format(
                    identifier=self.definition_identifier,
                    variant=mapping.get("identifier"),
                    error=exception
                )
            )

        try:
            if "constraints" in mapping.keys():
                mapping["constraints"] = [
                    wiz.utility.get_requirement(requirement)
                    for requirement in mapping["constraints"]
                ]

        except wiz.exception.InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "The definition '{identifier}' [{variant}] contains an "
                "incorrect package constraint [{error}]".format(
                    identifier=self.definition_identifier,
                    variant=mapping.get("identifier"),
                    error=exception
                )
            )

        super(_Variant, self).__init__(mapping)

    def copy(self, *args, **kwargs):
        """Return copy of instance."""
        mapping = dict(*args, **kwargs)
        mapping["definition"] = self.definition_identifier
        return super(_Variant, self).copy(**mapping)

    @property
    def _ordered_keywords(self):
        """Return ordered keywords."""
        return [
            "identifier",
            "command",
            "environ",
            "requirements",
            "constraints"
        ]

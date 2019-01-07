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


def fetch(paths, system_mapping=None, max_depth=None):
    """Return mapping from all definitions available under *paths*.

    A definition mapping should be in the form of::

        {
            "command": {
                "fooExe": "foo",
                ...
            },
            "package": {
                "__namespace__": {
                    "bar": {"test"}
                },
                "foo": {
                    "1.1.0": <Definition(identifier="foo", version="1.1.0")>,
                    "1.0.0": <Definition(identifier="foo", version="1.0.0")>,
                    "0.1.0": <Definition(identifier="foo", version="0.1.0")>,
                    ...
                },
                "test::bar": {
                    "0.1.0": <Definition(identifier="bar", version="0.1.0")>,
                    ...
                },
                ...
            },
            "implicit-packages": [
                "bar==0.1.0",
                ...
            ]
        }

    *system_mapping* could be a mapping of the current system which will filter
    out non compatible definitions. The mapping should have been retrieved via
    :func:`wiz.system.query`.

    """
    mapping = {
        wiz.symbol.PACKAGE_REQUEST_TYPE: {},
        wiz.symbol.COMMAND_REQUEST_TYPE: {},
    }

    # Record definitions which should be implicitly used.
    implicit_identifiers = []
    implicit_package_mapping = {}

    for definition in discover(
        paths, system_mapping=system_mapping, max_depth=max_depth
    ):
        _add_to_mapping(definition, mapping[wiz.symbol.PACKAGE_REQUEST_TYPE])

        # Record commands from definition.
        for command in definition.command.keys():
            mapping[wiz.symbol.COMMAND_REQUEST_TYPE][command] = (
                definition.identifier
            )

        # Record package identifiers which should be used implicitly in context.
        if definition.get("auto-use"):
            implicit_identifiers.append(definition.qualified_identifier)
            _add_to_mapping(definition, implicit_package_mapping)

    # Extract implicit package requests.
    mapping[wiz.symbol.IMPLICIT_PACKAGE] = _extract_implicit_requests(
        implicit_identifiers, implicit_package_mapping
    )

    wiz.history.record_action(
        wiz.symbol.DEFINITIONS_COLLECTION_ACTION,
        registries=paths, max_depth=max_depth, definition_mapping=mapping
    )

    return mapping


def _add_to_mapping(definition, mapping):
    """Mutate package *mapping* to add *definition*

    The mutated mapping should be in the form of::

        {
            "foo": {
                "1.1.0": <Definition(identifier="foo", version="1.1.0")>,
                "1.0.0": <Definition(identifier="foo", version="1.0.0")>,
                "0.1.0": <Definition(identifier="foo", version="0.1.0")>,
                ...
            },
            ...
        }

    """
    identifier = definition.identifier
    if definition.namespace is not None:
        mapping.setdefault("__namespace__", {})
        mapping["__namespace__"].setdefault(identifier, set())
        mapping["__namespace__"][identifier].add(definition.namespace)

    qualified_identifier = definition.qualified_identifier
    version = str(definition.version)

    mapping.setdefault(qualified_identifier, {})
    mapping[qualified_identifier].setdefault(version, {})
    mapping[qualified_identifier][version] = definition


def _extract_implicit_requests(identifiers, mapping):
    """Extract requests from definition *identifiers* and package *mapping*.

    Package requests are returned in inverse order of discovery to give priority
    to the latest discovered

    *identifiers* should be a list of definition identifiers sorted in order of
    discovery.

    *mapping* should be a mapping regrouping all implicit package definitions.
    It should be in the form of::

        {
            "__namespace__": {
                "bar": {"test"}
            },
            "foo": {
                "1.1.0": <Definition(identifier="foo", version="1.1.0")>,
                "1.0.0": <Definition(identifier="foo", version="1.0.0")>,
                "0.1.0": <Definition(identifier="foo", version="0.1.0")>,
                ...
            },
            "test::bar": {
                "0.1.0": <Definition(identifier="bar", version="0.1.0")>,
                ...
            },
            ...
        }


    """
    requests = []

    for identifier in sorted(
        (_id for _id in mapping.keys() if _id != "__namespace__"),
        key=lambda _id: identifiers.index(_id), reverse=True
    ):
        requirement = wiz.utility.get_requirement(identifier)
        definition = query(requirement, mapping)
        requests.append(definition.qualified_version_identifier)

    return requests


def query(requirement, definition_mapping, namespace_hints=None):
    """Return best matching definition version from *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available definition
    associated with their unique identifier.

    *namespace_hints* is a set which provides hints to select a default
    namespace if necessary.

    :exc:`wiz.exception.RequestNotFound` is raised if the requirement can not
    be resolved.

    """
    identifier = requirement.name

    # Extend identifier with namespace if necessary.
    namespace_mapping = definition_mapping.get("__namespace__", {})
    if identifier not in definition_mapping and not identifier.count("::"):
        _namespace = _guess_default_namespace(
            identifier, namespace_mapping,
            namespace_hints=namespace_hints
        )

        if _namespace is not None:
            identifier = "{}::{}".format(_namespace, identifier)

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


def _guess_default_namespace(
    identifier, namespace_mapping, namespace_hints=None
):
    """Return namespace corresponding to *identifier* if available.

    *identifier* should be a definition identifier.

    *namespace_mapping* should be a mapping in the form of::

        {
            "foo": ["namespace1", "namespace2"]
            ...
        }

    *namespace_hints* is a list which provides hints to select a default
    namespace if necessary.

    """
    # Use the list of initial requests from the namespace_mapping as additional
    # namespace hints to help determining an appropriate namespace.
    if namespace_hints is None:
        namespace_hints = namespace_mapping.keys()
    else:
        namespace_hints.update(namespace_mapping.keys())

    _namespaces = namespace_mapping.get(identifier, [])
    if len(_namespaces) == 0:
        return

    # Filter out some namespaces from hints if necessary.
    if len(_namespaces) > 1:
        _namespaces = [
            namespace for namespace in _namespaces
            if not namespace_hints or namespace in namespace_hints
        ]

    if len(_namespaces) == 1:
        return _namespaces.pop()

    raise wiz.exception.RequestNotFound(
        "Impossible to guess default namespace for '{definition}' "
        "[available: {namespaces}].".format(
            definition=identifier,
            namespaces=", ".join(sorted(namespace_mapping.get(identifier, [])))
        )
    )


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

    definition = definition.sanitized()

    file_name = wiz.utility.compute_file_name(definition)
    file_path = os.path.join(os.path.abspath(path), file_name)
    wiz.filesystem.export(file_path, definition.encode(), overwrite=overwrite)
    return file_path


def discover(paths, system_mapping=None, max_depth=None):
    """Discover and yield all definitions found under *paths*.

    *system_mapping* could be a mapping of the current system which will filter
    out non compatible definitions. The mapping should have been retrieved via
    :func:`wiz.system.query`.

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

                _path = os.path.join(base, filename)

                # Load and validate the definition.
                try:
                    definition = load(_path, mapping={"registry": path})

                except (
                    IOError, ValueError, TypeError,
                    wiz.exception.WizError
                ):
                    logger.warning(
                        "Error occurred trying to load definition from {!r}"
                        .format(_path),
                        traceback=True
                    )
                    continue

                # Skip definition if an incompatible system if set.
                if (
                    system_mapping is not None and
                    not wiz.system.validate(definition, system_mapping)
                ):
                    continue

                # Skip definition if "disabled" keyword is set to True.
                if definition.get("disabled", False):
                    _id = definition.qualified_version_identifier
                    logger.warning("Definition '{}' is disabled".format(_id))
                    continue

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

    mapping.setdefault("definition-location", path)

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

        if "variants" in mapping.keys():
            mapping["variants"] = [
                _Variant(
                    dict(definition=mapping.get("identifier"), **variant)
                ) for variant in mapping["variants"]
            ]

        super(Definition, self).__init__(mapping)

    def sanitized(self):
        """Return definition instance without keywords added at load time.

        These keyword must be removed before exporting the definition into a
        file.

        """
        _definition = self.remove("definition-location")
        _definition = _definition.remove("registry")
        return _definition

    @property
    def qualified_identifier(self):
        """Return qualified identifier with optional namespace."""
        if self.namespace is not None:
            return "{}::{}".format(self.namespace, self.identifier)
        return self.identifier

    @property
    def version_identifier(self):
        """Return version identifier."""
        if self.version != wiz.symbol.UNKNOWN_VALUE:
            return "{}=={}".format(self.identifier, self.version)
        return self.identifier

    @property
    def qualified_version_identifier(self):
        """Return qualified version identifier with optional namespace."""
        if self.namespace is not None:
            return "{}::{}".format(self.namespace, self.version_identifier)
        return self.version_identifier

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
            "namespace",
            "description",
            "registry",
            "definition-location",
            "install-location",
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
        super(_Variant, self).__init__(mapping)

    def _label(self):
        """Return object label to include in exception messages."""
        return "The definition '{identifier}' [{variant}]".format(
            identifier=self.definition_identifier,
            variant=self.identifier
        )

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

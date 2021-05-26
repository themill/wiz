# :coding: utf-8

from __future__ import absolute_import
import os
import copy
import json
import collections
import logging

import ujson

import wiz.exception
import wiz.filesystem
import wiz.history
import wiz.package
import wiz.symbol
import wiz.system
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

    :param paths: List of registry paths to recursively fetch
        :class:`definitions <Definition>` from.

    :param system_mapping: Mapping defining the current system to filter
        out non compatible definitions. Default is None, which means that the
        current system mapping will be :func:`queried <wiz.system.query>`.

    :param max_depth: Limited recursion value to search for :class:`definitions
        <Definition>`. Default is None, which means that all  sub-trees will be
        visited.

    :return: Definition mapping.

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
                definition.qualified_identifier
            )

        # Record package identifiers which should be used implicitly in context.
        if definition.auto_use:
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

    :param definition: Instance of :class:`Definition`.

    :param mapping: Mapping to mutate.

    """
    identifier = definition.identifier
    if definition.namespace is not None:
        mapping.setdefault("__namespace__", {})
        mapping["__namespace__"].setdefault(identifier, set())
        mapping["__namespace__"][identifier].add(definition.namespace)

    qualified_identifier = definition.qualified_identifier
    version = str(definition.version or wiz.symbol.UNSET_VALUE)

    mapping.setdefault(qualified_identifier, {})
    mapping[qualified_identifier].setdefault(version, {})
    mapping[qualified_identifier][version] = definition


def _extract_implicit_requests(identifiers, mapping):
    """Extract requests from definition *identifiers* and package *mapping*.

    Package requests are returned in inverse order of discovery to give priority
    to the latest discovered

    :param identifiers: List of definition identifiers sorted in order of
        discovery.

    :param mapping: Mapping regrouping all implicit package definitions.
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

    :return: List of request strings.

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


def query(requirement, definition_mapping, namespace_counter=None):
    """Return best matching definition version from *requirement*.

    :param requirement: Instance of :class:`packaging.requirements.Requirement`.

    :param definition_mapping: Mapping regrouping all available definitions
        associated with their unique identifier.

    :param namespace_counter: instance of :class:`collections.Counter`
        which indicates occurrence of namespaces used as hints for package
        identification. Default is None.

    :return: Instance of :class:`Definition`.

    :raise: :exc:`wiz.exception.RequestNotFound` if the requirement can not
        be resolved.

    """
    identifier = requirement.name

    variant_identifier = None

    # Extract variant if necessary.
    if len(requirement.extras) > 0:
        variant_identifier = next(iter(requirement.extras))

    # Extend identifier with namespace if necessary.
    if wiz.symbol.NAMESPACE_SEPARATOR not in identifier:
        identifier = _guess_qualified_identifier(
            identifier, definition_mapping, namespace_counter=namespace_counter
        )

    # If identifier starts with namespace separator, that means the identifier
    # without namespace is required.
    if identifier.startswith(wiz.symbol.NAMESPACE_SEPARATOR):
        identifier = identifier[2:]

    if identifier not in definition_mapping:
        raise wiz.exception.RequestNotFound(
            "The requirement '{}' could not be resolved.".format(requirement)
        )

    definition = None

    # Extract all versions from definitions.
    versions = [
        _definition.version or wiz.symbol.UNSET_VALUE
        for _definition in definition_mapping[identifier].values()
    ]

    if wiz.symbol.UNSET_VALUE in versions and len(versions) > 1:
        raise wiz.exception.RequestNotFound(
            "Impossible to retrieve the best matching definition for "
            "'{}' as non-versioned and versioned definitions have "
            "been fetched.".format(identifier)
        )

    # Sort the definition versions so that the highest one is first.
    versions = sorted(versions, reverse=True)

    # Get the best matching definition by sorting versions so that the highest
    # one is first.
    for version in sorted(versions, reverse=True):
        _definition = definition_mapping[identifier][str(version)]

        # Skip if the variant identifier required is not found in definition.
        if variant_identifier and not any(
            variant_identifier == variant.identifier
            for variant in _definition.variants
        ):
            continue

        if (
            _definition.version is None
            or _definition.version in requirement.specifier
        ):
            definition = _definition
            break

    if definition is None:
        raise wiz.exception.RequestNotFound(
            "The requirement '{}' could not be resolved.".format(requirement)
        )

    return definition


def _guess_qualified_identifier(
    identifier, definition_mapping, namespace_counter=None
):
    """Return qualified identifier with default namespace if possible.

    Rules are as follow:

    * If definition does not have any namespaces, return identifier;
    * If definition has one namespace, return identifier with namespace;
    * If definition has one namespace and also exists without identifier,
      return the one without a namespace;
    * If definition has several namespaces available, use the
      *namespace_counter* to filter out namespaces which don't have the maximum
      occurrence number. If only one namespace remains, use this one;
    * If definition still has several namespaces available after checking
      occurrences, if one of these namespaces is equal to the identifier (e.g.
      "maya::maya"), return that one.
    * If definition still has several namespaces after exhausting all other
      options, raise :exc:`wiz.exception.RequestNotFound`.

    :param identifier: Unique identifier of a definition.

    :param definition_mapping: Mapping regrouping all available definitions
        associated with their unique identifier.

    :param namespace_counter: instance of :class:`collections.Counter`
        which indicates occurrence of namespaces used as hints for package
        identification. Default is None.

    :return: Qualified identifier (e.g. "namespace::foo")

    :raise: :exc:`wiz.exception.RequestNotFound` if the default namespace can
        not be guessed.

    """
    namespace_mapping = definition_mapping.get("__namespace__", {})

    _namespaces = list(namespace_mapping.get(identifier, []))

    # If no namespace are found, just return identifier unchanged.
    if len(_namespaces) == 0:
        return identifier

    max_occurrence = 0

    # Fetch number of occurrence of the namespace for counter if available.
    if namespace_counter is not None:
        max_occurrence = max([namespace_counter[name] for name in _namespaces])

    # If more than one namespace is available, attempt to use counter to only
    # keep those which are used the most.
    if len(_namespaces) > 1 and max_occurrence > 0:
        _namespaces = [
            namespace for namespace in _namespaces
            if namespace_counter[namespace] == max_occurrence
        ]

    # If more than one namespace is available and one namespace is identical to
    # the definition identifier (e.g. "maya::maya"), it will be selected by
    # default.
    if len(_namespaces) > 1 and any(name == identifier for name in _namespaces):
        _namespaces = [identifier]

    # If more than one namespace is available or if we didn't need to shrink the
    # namespace list from occurrences and definition exists without a namespace,
    # it will be selected by default.
    if (
        (len(_namespaces) > 1 or max_occurrence <= 1)
        and identifier in definition_mapping
    ):
        return identifier

    if len(_namespaces) == 1:
        return _namespaces.pop() + wiz.symbol.NAMESPACE_SEPARATOR + identifier

    raise wiz.exception.RequestNotFound(
        "Cannot guess default namespace for '{definition}' "
        "[available: {namespaces}].".format(
            definition=identifier,
            namespaces=", ".join(sorted(_namespaces))
        )
    )


def export(path, data, overwrite=False):
    """Export *definition* as a :term:`JSON` file to *path*.

    :param path: Target path to save the exported definition into.

    :param data: Instance of :class:`wiz.definition.Definition` or a mapping in
        the form of::

            {
                "identifier": "foo",
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

    :param overwrite: Indicate whether existing definitions in the target path
        will be overwritten. Default is False.

    :return: Path to exported definition.

    :raise: :exc:`wiz.exception.IncorrectDefinition` if *data* is a mapping that
        cannot create a valid instance of :class:`wiz.definition.Definition`.

    :raise: :exc:`wiz.exception.FileExists` if definition already exists in
        *path* and overwrite is False.

    :raise: :exc:`OSError` if the definition can not be exported in *path*.

    .. warning::

        Ensure that the *data* :ref:`identifier <definition/identifier>`,
        :ref:`namespace <definition/namespace>`, :ref:`version
        <definition/version>` and :ref:`system requirement <definition/system>`
        are unique in the registry.

        Each :ref:`command <definition/command>` must also be unique in the
        registry.

    """
    if not isinstance(data, Definition):
        definition = wiz.definition.Definition(data)
    else:
        definition = data

    file_name = wiz.utility.compute_file_name(definition)
    file_path = os.path.join(os.path.abspath(path), file_name)
    wiz.filesystem.export(file_path, definition.encode(), overwrite=overwrite)
    return file_path


def discover(paths, system_mapping=None, max_depth=None):
    """Discover and yield all definitions found under *paths*.

    :param paths: List of registry paths to recursively fetch
        :class:`definitions <Definition>` from.

    :param system_mapping: Mapping of the current system which will filter out
        non compatible definitions. The mapping should have been retrieved via
        :func:`wiz.system.query`.

    :param max_depth: Limited recursion value to search for :class:`definitions
        <Definition>`. Default is None, which means that all  sub-trees will be
        visited.

    :return: Generator which yield all :class:`definitions <Definition>`.

    """
    logger = logging.getLogger(__name__ + ".discover")

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
                    definition = load(_path, registry_path=path)

                except (
                    IOError, ValueError, TypeError,
                    wiz.exception.WizError
                ):
                    logger.warning(
                        "Error occurred trying to load definition from {!r}"
                        .format(_path)
                    )
                    continue

                # Skip definition if an incompatible system if set.
                if (
                    system_mapping is not None and
                    not wiz.system.validate(definition, system_mapping)
                ):
                    continue

                # Skip definition if "disabled" keyword is set to True.
                if definition.disabled:
                    _id = definition.qualified_version_identifier
                    logger.warning("Definition '{}' is disabled".format(_id))
                    continue

                yield definition


def load(path, mapping=None, registry_path=None):
    """Load and return a definition from *path*.

    :param path: :term:`JSON` file path which contains a definition.

    :param mapping: Mapping which will augment the data leading to the creation
        of the definition. Default is None.

    :param registry_path: Path to the registry which contains the definition.
        Default is None.

    :return: Instance of :class:`Definition`.

    :raise: :exc:`wiz.exception.IncorrectDefinition` if the definition is
        incorrect.

    """
    if mapping is None:
        mapping = {}

    with open(path, "r") as stream:
        definition_data = ujson.load(stream)
        definition_data.update(mapping)

        return Definition(
            definition_data,
            path=path,
            registry_path=registry_path,
            copy_data=False
        )


class Definition(object):
    """Definition object."""

    def __init__(
        self, data, path=None, registry_path=None, copy_data=True
    ):
        """Initialize definition from input *data* mapping.

        :param data: Data definition mapping.

        :param path: Path to the definition :term:`JSON` file used to create the
            definition if available. Default is None.

        :param registry_path: Path to the registry from which the definition
            where fetched if available. Default is None.

        :param copy_data: Indicate whether input *data* will be copied to
            prevent mutating it. Default is True.

        :raise: :exc:`wiz.exception.IncorrectDefinition` if the *data* mapping
            is incorrect.

        .. warning::

            "requirements" and "conditions" values will not get validated when
            constructing the instance for performance reason. Therefore,
            accessing these values could raise an error when data is incorrect::

                >>> definition = Definition({
                ...     "identifier": "foo",
                ...     "requirements": ["!!!"],
                ... })
                >>> print(definition.requirements)

                InvalidRequirement: The requirement '!!!' is incorrect

        .. seealso:: :ref:`definition`

        """
        wiz.validator.validate_definition(data)

        # Ensure that input data is not mutated if requested.
        if copy_data:
            data = copy.deepcopy(data)

        self._data = data
        self._path = path
        self._registry_path = registry_path

        # Store values that needs to be constructed.
        self._cache = {}

    def __repr__(self):
        """Representing a Definition."""
        return (
            "<Definition id='{0}' version='{1}'>".format(
                self.qualified_identifier,
                self.version
            )
        )

    @property
    def path(self):
        """Return path to definition if available.

        :return: Definition :term:`JSON` path or None.

        """
        return self._path

    @property
    def registry_path(self):
        """Return registry path containing the definition if available.

        :return: Registry path or None.

        """
        return self._registry_path

    @property
    def identifier(self):
        """Return definition identifier.

        :return: String value (e.g. "foo").

        .. seealso:: :ref:`definition/identifier`

        """
        return self._data["identifier"]

    @property
    def version(self):
        """Return definition version.

        :return: Instance of :class:`packaging.version.Version` or None.

        :raise: :exc:`wiz.exception.InvalidVersion` if the version is incorrect.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        .. seealso:: :ref:`definition/version`

        """
        version = self._data.get("version")

        # Create cache value if necessary.
        if version is not None and self._cache.get("version") is None:
            self._cache["version"] = wiz.utility.get_version(version)

        # Return cached value.
        return self._cache.get("version")

    @property
    def qualified_identifier(self):
        """Return qualified identifier with optional namespace.

        :return: String value (e.g. "namespace::foo").

        """
        if self.namespace is not None:
            return "{}::{}".format(self.namespace, self.identifier)
        return self.identifier

    @property
    def version_identifier(self):
        """Return version identifier.

        :return: String value (e.g. "foo==0.1.0").

        """
        if self.version is not None:
            return "{}=={}".format(self.identifier, self.version)
        return self.identifier

    @property
    def qualified_version_identifier(self):
        """Return qualified version identifier with optional namespace.

        :return: String value (e.g. "namespace::foo==0.1.0").

        """
        if self.namespace is not None:
            return "{}::{}".format(self.namespace, self.version_identifier)
        return self.version_identifier

    @property
    def description(self):
        """Return definition description.

        :return: String value or None.

        .. seealso:: :ref:`definition/description`

        """
        return self._data.get("description")

    @property
    def namespace(self):
        """Return definition namespace.

        :return: String value or None.

        .. seealso:: :ref:`definition/namespace`

        """
        return self._data.get("namespace")

    @property
    def auto_use(self):
        """Return whether definition should be automatically requested.

        :return: Boolean value.

        .. seealso:: :ref:`definition/auto-use`

        """
        return self._data.get("auto-use", False)

    @property
    def disabled(self):
        """Return whether definition is disabled.

        :return: Boolean value.

        .. seealso:: :ref:`definition/disabled`

        """
        return self._data.get("disabled", False)

    @property
    def install_root(self):
        """Return root installation path.

        :return: Directory path or None.

        .. seealso:: :ref:`definition/install_root`

        """
        return self._data.get("install-root")

    @property
    def install_location(self):
        """Return installation path.

        :return: Directory path or None.

        .. seealso:: :ref:`definition/install_location`

        """
        return self._data.get("install-location")

    @property
    def environ(self):
        """Return environment variable mapping.

        :return: Dictionary value.

        .. seealso:: :ref:`definition/environ`

        """
        return self._data.get("environ", {})

    @property
    def command(self):
        """Return command mapping.

        :return: Dictionary value.

        .. seealso:: :ref:`definition/command`

        """
        return self._data.get("command", {})

    @property
    def system(self):
        """Return system requirement mapping.

        :return: Dictionary value.

        .. seealso:: :ref:`definition/system`

        """
        return self._data.get("system", {})

    @property
    def requirements(self):
        """Return list of requirements.

        :return: List of :class:`packaging.requirements.Requirement` instances.

        :raise: :exc:`wiz.exception.InvalidRequirement` if one requirement is
            incorrect.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        .. seealso:: :ref:`definition/requirements`

        """
        requirements = self._data.get("requirements")

        # Create cache value if necessary.
        if requirements is not None and self._cache.get("requirements") is None:
            self._cache["requirements"] = [
                wiz.utility.get_requirement(requirement)
                for requirement in requirements
            ]

        # Return cached value.
        return self._cache.get("requirements", [])

    @property
    def conditions(self):
        """Return list of conditions.

        :return: List of :class:`packaging.requirements.Requirement` instances.

        :raise: :exc:`wiz.exception.InvalidRequirement` if one requirement is
            incorrect.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        .. seealso:: :ref:`definition/conditions`

        """
        conditions = self._data.get("conditions")

        # Create cache value if necessary.
        if conditions is not None and self._cache.get("conditions") is None:
            self._cache["conditions"] = [
                wiz.utility.get_requirement(condition)
                for condition in conditions
            ]

        # Return cached value.
        return self._cache.get("conditions", [])

    @property
    def variants(self):
        """Return list of conditions.

        :return: List of :class:`Variant` instances.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        .. seealso:: :ref:`definition/variants`

        """
        variants = self._data.get("variants")

        # Create cache value if necessary.
        if variants is not None and self._cache.get("variants") is None:
            self._cache["variants"] = [
                Variant(variant, definition_identifier=self.identifier)
                for variant in variants
            ]

        # Return cached value.
        return self._cache.get("variants", [])

    def set(self, element, value):
        """Returns copy of instance with *element* set to *value*.

        :param element: Keyword to add or update in mapping.

        :param value: New value to set as keyword value.

        :return: New updated mapping.

        """
        data = self.data()
        data[element] = value

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def update(self, element, value):
        """Returns copy of instance with *element* mapping updated with *value*.

        :param element: keyword associated to a dictionary.

        :param value: mapping to update *element*  dictionary with.

        :return: New updated mapping.

        :raise: :exc:`ValueError` if *element* is not a dictionary.

        """
        data = self.data()
        data.setdefault(element, {})

        if not isinstance(data[element], dict):
            raise ValueError(
                "Impossible to update '{}' as it is not a "
                "dictionary.".format(element)
            )

        data[element].update(value)

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def extend(self, element, values):
        """Returns copy of instance with *element* list extended with *values*.

        :param element: keyword associated to a list.

        :param values: Values to extend *element* list with.

        :return: New updated mapping.

        :raise: :exc:`ValueError` if *element* is not a list.

        """
        data = self.data()
        data.setdefault(element, [])

        if not isinstance(data[element], list):
            raise ValueError(
                "Impossible to extend '{}' as it is not a list.".format(element)
            )

        data[element].extend(values)

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def insert(self, element, value, index):
        """Returns copy of instance with *value* inserted in *element* list.

        :param element: keyword associated to a list.

        :param value: Value which will be added to the *element* list

        :param index: Index number at which the *value* should be inserted.

        :return: New updated mapping.

        :raise: :exc:`ValueError` if *element* is not a list.

        """
        data = self.data()
        data.setdefault(element, [])

        if not isinstance(data[element], list):
            raise ValueError(
                "Impossible to insert '{}' in '{}' as it is not "
                "a list.".format(value, element)
            )

        data[element].insert(index, value)

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def remove(self, element):
        """Returns copy of instance without *element*.

        :param element: keyword to remove from mapping.

        :return: New updated mapping or "self" if *element* didn't exist in
            mapping.

        """
        data = self.data()
        if element not in data.keys():
            return self

        del data[element]

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def remove_key(self, element, value):
        """Returns copy of instance without key *value* from *element* mapping.

        If *element* mapping is empty after removing *value*, the *element* key
        will be removed.

        :param element: keyword associated to a dictionary.

        :param value: Value to remove from *element* dictionary.

        :return: New updated mapping.

        :raise: :exc:`ValueError` if *element* is not a dictionary.

        """
        data = self.data()
        if element not in data.keys():
            return self

        if not isinstance(data[element], dict):
            raise ValueError(
                "Impossible to remove key from '{}' as it is not a "
                "dictionary.".format(element)
            )

        if value not in data[element].keys():
            return self

        del data[element][value]
        if len(data[element]) == 0:
            del data[element]

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def remove_index(self, element, index):
        """Returns copy of instance without *index* from *element* list.

        If *element* list is empty after removing *index*, the *element* key
        will be removed.

        :param element: keyword associated to a list.

        :param index: Index to remove from *element* list.

        :return: New updated mapping.

        :raise: :exc:`ValueError` if *element* is not a list.

        """
        data = self.data()
        if element not in data.keys():
            return self

        if not isinstance(data[element], list):
            raise ValueError(
                "Impossible to remove index from '{}' as it is not a "
                "list.".format(element)
            )

        if index >= len(data[element]):
            return self

        del data[element][index]
        if len(data[element]) == 0:
            del data[element]

        return Definition(
            data, path=self._path,
            registry_path=self._registry_path,
            copy_data=False
        )

    def data(self, copy_data=True):
        """Return definition data used to created the definition instance.

        :param copy_data: Indicate whether definition data will be copied to
            prevent mutating it. Default is True.

        :return: Definition data mapping.

        """
        if not copy_data:
            return self._data
        return copy.deepcopy(self._data)

    def ordered_data(self, copy_data=True):
        """Return copy of definition data as :class:`collections.OrderedDict`.

        Definition keywords will be sorted as follows:

            1. identifier
            2. version
            3. namespace
            4. description
            5. install-root
            6. install-location
            7. auto-use
            8. disabled
            9. system
            10. command
            11. environ
            12. requirements
            13. conditions
            14. variants

        :ref:`System <definition/system>` keywords will be sorted as follows:

            1. platform
            2. os
            3. arch

        Each :ref:`variant <definition/variants>` mapping will be sorted as
        follows:

            1. identifier
            2. install-location
            3. command
            4. environ
            5. requirements

        :param copy_data: Indicate whether definition data will be copied to
            prevent mutating it. Default is True.

        :return: Instance of :class:`collections.OrderedDict`.

        """
        definition_keywords = [
            "identifier", "version", "namespace", "description",
            "install-root", "install-location", "auto-use", "disabled",
            "system", "command", "environ", "requirements", "conditions",
            "variants"
        ]

        system_keywords = ["platform", "os", "arch"]

        variant_keywords = [
            "identifier", "install-location", "command", "environ",
            "requirements"
        ]

        def _create_ordered_dict(mapping, keywords):
            """Return ordered dictionary from mapping according to keywords.
            """
            content = collections.OrderedDict()

            for keyword in keywords:
                if keyword not in mapping:
                    continue

                if keyword == "system":
                    content[keyword] = _create_ordered_dict(
                        mapping["system"], system_keywords
                    )

                elif keyword == "variants":
                    content[keyword] = [
                        _create_ordered_dict(variant, variant_keywords)
                        for variant in mapping["variants"]
                    ]

                elif isinstance(mapping[keyword], dict):
                    content[keyword] = collections.OrderedDict(
                        sorted(mapping[keyword].items())
                    )

                else:
                    content[keyword] = mapping[keyword]

            return content

        return _create_ordered_dict(
            self.data(copy_data=copy_data), definition_keywords
        )

    def encode(self):
        """Return serialized definition data.

        :class:`collections.OrderedDict` instance as returned by
        :meth:`ordered_data` is being used.

        :return: Serialized mapping.

        """
        return json.dumps(
            self.ordered_data(),
            indent=4,
            separators=(",", ": "),
            ensure_ascii=False
        )


class Variant(object):
    """Definition variant object."""

    def __init__(self, data, definition_identifier):
        """Initialize definition variant.

        :param data: Variant data definition mapping.

        :param definition_identifier: Identifier of the definition containing
            the variant data.

        .. warning::

            "requirements" values will not get validated when constructing the
            instance for performance reason. Therefore, accessing this value
            could raise an error when data is incorrect::

                >>> variant = Variant(
                ...     {
                ...         "identifier": "variant1",
                ...         "requirements": ["!!!"],
                ...     },
                ...     definition_identifier="foo"
                ... )
                >>> print(variant.requirements)

                InvalidRequirement: The requirement '!!!' is incorrect

        .. seealso:: :ref:`definition/variants`

        """
        self._data = data
        self._definition_identifier = definition_identifier

        # Store values that needs to be constructed.
        self._cache = {}

    @property
    def identifier(self):
        """Return variant identifier.

        :return: String value (e.g. "variant1").

        """
        return self._data["identifier"]

    @property
    def definition_identifier(self):
        """Return definition identifier.

        :return: String value (e.g. "foo").

        """
        return self._definition_identifier

    @property
    def install_location(self):
        """Return installation path.

        :return: Directory path or None.

        .. seealso:: :ref:`definition/install_location`

        """
        return self._data.get("install-location")

    @property
    def environ(self):
        """Return environment variable mapping.

        :return: Dictionary value.

        .. seealso:: :ref:`definition/environ`

        """
        return self._data.get("environ", {})

    @property
    def command(self):
        """Return command mapping.

        :return: Dictionary value.

        .. seealso:: :ref:`definition/command`

        """
        return self._data.get("command", {})

    @property
    def requirements(self):
        """Return list of requirements.

        :return: List of :class:`packaging.requirements.Requirement` instances.

        :raise: :exc:`wiz.exception.InvalidRequirement` if one requirement is
            incorrect.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        .. seealso:: :ref:`definition/requirements`

        """
        requirements = self._data.get("requirements")

        # Create cache value if necessary.
        if requirements is not None and self._cache.get("requirements") is None:
            self._cache["requirements"] = [
                wiz.utility.get_requirement(requirement)
                for requirement in requirements
            ]

        # Return cached value.
        return self._cache.get("requirements", [])

    def data(self, copy_data=True):
        """Return variant data used to created the variant instance.

        :param copy_data: Indicate whether definition data will be copied to
            prevent mutating it. Default is True.

        :return: Variant data mapping.

        """
        if not copy_data:
            return self._data
        return copy.deepcopy(self._data)

# :coding: utf-8

from __future__ import absolute_import
import functools
import logging

import wiz.definition
import wiz.environ
import wiz.exception
import wiz.history
import wiz.symbol


def extract(requirement, definition_mapping, namespace_counter=None):
    """Extract list of :class:`Package` instances from *requirement*.

    The best matching :class:`~wiz.definition.Definition` version instances
    corresponding to the *requirement* will be used.

    If this definition contains variants, a :class:`Package` instance will be
    returned for each combined variant.

    :param requirement: Instance of :class:`packaging.requirements.Requirement`.

    :param definition_mapping: Mapping regrouping all available definitions
        associated with their unique identifier.

    :param namespace_counter: instance of :class:`collections.Counter`
        which indicates occurrence of namespaces used as hints for package
        identification. Default is None.

    :return: List of :class:`Package` instances.

    """
    definition = wiz.definition.query(
        requirement, definition_mapping,
        namespace_counter=namespace_counter
    )

    # Extract and return the requested variant if necessary.
    if len(requirement.extras) > 0:
        variant = next(iter(requirement.extras))
        return [create(definition, variant_identifier=variant)]

    # Simply return the package corresponding to the main definition if no
    # variants are available.
    elif len(definition.variants) == 0:
        return [create(definition)]

    # Otherwise, extract and return all possible variants.
    else:
        return [
            create(definition, variant_identifier=variant.identifier)
            for variant in definition.variants
        ]


def extract_context(packages, environ_mapping=None):
    """Return combined mapping extracted from *packages*.

    Example::

        >>> extract_context(packages)
        {
            "command": {
                "app": "AppExe"
                ...
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            },
        }

    :param packages: List of :class:`Package` instances. it should be ordered
        from the less important to the most important so that the later are
        prioritized over the first.

    :param environ_mapping: Mapping of environment variables which would
        be augmented. Default is None.

    :return: Context mapping.

    """

    def _combine(combined_mapping, package):
        """Return intermediate context combining both extracted results."""
        identifier = package.identifier
        _environ = combine_environ_mapping(
            identifier, combined_mapping.get("environ", {}),
            package.localized_environ()
        )
        _command = combine_command_mapping(
            identifier, combined_mapping.get("command", {}),
            package.command
        )
        return dict(command=_command, environ=_environ)

    mapping = functools.reduce(
        _combine, packages, dict(environ=environ_mapping or {})
    )
    mapping["environ"] = wiz.environ.sanitize(mapping.get("environ", {}))

    wiz.history.record_action(
        wiz.symbol.CONTEXT_EXTRACTION_ACTION,
        packages=packages, initial=environ_mapping, context=mapping
    )
    return mapping


def combine_environ_mapping(package_identifier, mapping1, mapping2):
    """Return combined environ mapping from *mapping1* and *mapping2*.

    Each variable name from both mappings will be combined into a final value.
    If a variable is only contained in one of the mapping, its value will be
    kept in the combined mapping.

    If the variable exists in both mappings, the value from *mapping2* must
    reference the variable name for the value from *mapping1* to be included
    in the combined mapping::

        >>> combine_environ_mapping(
        ...     "combined_package",
        ...     {"key": "value2"},
        ...     {"key": "value1:${key}"}
        ... )

        {"key": "value1:value2"}

    Otherwise the value from *mapping2* will override the value from
    *mapping1*::

        >>> combine_environ_mapping(
        ...     "combined_package",
        ...     {"key": "value2"},
        ...     {"key": "value1"}
        ... )

        warning: The 'key' variable is being overridden in 'combined_package'.
        {"key": "value1"}

    If other variables from *mapping1* are referenced in the value fetched
    from *mapping2*, they will be replaced as well::

        >>> combine_environ_mapping(
        ...     "combined_package",
        ...     {"PLUGIN": "/path/to/settings", "HOME": "/usr/people/me"},
        ...     {"PLUGIN": "${HOME}/.app:${PLUGIN}"}
        ... )

        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/settings"
        }

    :param package_identifier: Identifier of the combined package. It will
        be used to indicate whether any variable is overridden in the
        combination process.

    :param mapping1: Mapping containing environment variables.

    :param mapping2: Mapping containing environment variables.

    :return: Combined environment mapping.

    .. warning::

        This process will stringify all variable values.

    """
    logger = logging.getLogger(__name__ + ".combine_environ_mapping")

    mapping = {}

    for key in set(list(mapping1.keys()) + list(mapping2.keys())):
        value1 = mapping1.get(key)
        value2 = mapping2.get(key)

        if value2 is None:
            mapping[key] = str(value1)

        else:
            if value1 is not None and not wiz.environ.contains(value2, key):
                logger.warning(
                    "The '{key}' variable is being overridden "
                    "in '{identifier}'".format(
                        key=key, identifier=package_identifier
                    )
                )

            mapping[key] = wiz.environ.substitute(str(value2), mapping1)

    return mapping


def combine_command_mapping(package_identifier, mapping1, mapping2):
    """Return combined command mapping from *package1* and *package2*.

    If the command exists in both mappings, the value from *mapping2* will have
    priority over elements from *mapping1*::

        >>> combine_command_mapping(
        ...     "combined_package",
        ...     {"app": "App1.1 --run"},
        ...     {"app": "App2.1"}
        ... )

        {"app": "App2.1"}

    :param package_identifier: Identifier of the combined package. It will
        be used to indicate whether any variable is overridden in the
        combination process.

    :param mapping1: Mapping containing command aliased.

    :param mapping2: Mapping containing command aliased.

    :return: Combined command alias mapping.

    """
    logger = logging.getLogger(__name__ + ".combine_command_mapping")

    mapping = {}

    for command in set(list(mapping1.keys()) + list(mapping2.keys())):
        value1 = mapping1.get(command)
        value2 = mapping2.get(command)

        if value1 is not None and value2 is not None:
            logger.debug(
                "The '{key}' command is being overridden "
                "in '{identifier}'".format(
                    key=command, identifier=package_identifier
                )
            )
            mapping[command] = str(value2)

        else:
            mapping[command] = str(value1 or value2)

    return mapping


def create(definition, variant_identifier=None):
    """Create and return a package from *definition*.

    :param definition: Instance of :class:`wiz.definition.Definition`.

    :param variant_identifier: Unique identifier of variant in *definition* to
        create package from.

    :return: Instance of :class:`Package`.

    :raise: :exc:`wiz.exception.RequestNotFound` if *variant_identifier* is not
        a valid variant identifier of *definition*.

    """
    if variant_identifier is not None:
        for index, variant in enumerate(definition.variants):
            if variant_identifier == variant.identifier:
                return Package(definition, variant_index=index)

        raise wiz.exception.RequestNotFound(
            "The variant '{variant}' could not been resolved for "
            "'{definition}'.".format(
                variant=variant_identifier,
                definition=definition.qualified_version_identifier,
            )
        )

    return Package(definition)


class Package(object):
    """Package object."""

    def __init__(self, definition, variant_index=None):
        """Initialize package.

        :param definition: Instance of :class:`wiz.definition.Definition`.

        :param variant_index: Index number of the variant which will be used to
            create package instance if applicable. Default is None.

        :raise: :exc:`wiz.exception.PackageError` if the variant index is
            missing or incorrect.

        """
        self._definition = definition
        self._variant_index = variant_index

        # Store values that needs to be constructed.
        self._cache = {}

        # Store boolean value indicating whether the package conditions have
        # been processed
        self._conditions_processed = False

        if self._variant_index is None and len(self._definition.variants) > 0:
            raise wiz.exception.PackageError(
                "Package cannot be created from definition '{}' as no variant "
                "index is defined.".format(
                    self._definition.qualified_identifier
                )
            )

        if (
            self._variant_index is not None
            and self._variant_index + 1 > len(self._definition.variants)
        ):
            raise wiz.exception.PackageError(
                "Package cannot be created from definition '{}' with variant "
                "index #{}.".format(
                    self._definition.qualified_identifier,
                    self._variant_index
                )
            )

    def __repr__(self):
        """Representing a Package."""
        return "<Package id='{0}'>".format(self.identifier)

    @property
    def definition(self):
        """Return definition used to create package.

        :return: Instance of :class:`wiz.definition.Definition`.

        """
        return self._definition

    @property
    def identifier(self):
        """Return package identifier.

        :return: String value (e.g. "namespace::foo[variant1]==0.1.0").

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        """
        # Create cache value if necessary.
        if self._cache.get("identifier") is None:
            identifier = self._definition.identifier

            if self.variant_identifier is not None:
                identifier += "[{}]".format(self.variant_identifier)
            if self._definition.version:
                identifier += "=={}".format(self._definition.version)
            if self.namespace is not None:
                identifier = "{}::{}".format(self.namespace, identifier)

            self._cache["identifier"] = identifier

        # Return cached value.
        return self._cache["identifier"]

    @property
    def variant(self):
        """Return variant instance if applicable.

        :return: Instance of :class:`wiz.definition.Variant` or None.

        """
        if self._variant_index is not None:
            return self.definition.variants[self._variant_index]

    @property
    def variant_identifier(self):
        """Return variant identifier if applicable.

        :return: String value (e.g. "variant1") or None.

        """
        if self.variant is not None:
            return self.variant.identifier

    @property
    def version(self):
        """Return package version.

        :return: Instance of :class:`packaging.version.Version` or None.

        """
        return self._definition.version

    @property
    def description(self):
        """Return package description.

        :return: String value or None.

        """
        return self._definition.description

    @property
    def namespace(self):
        """Return package namespace.

        :return: String value or None.

        """
        return self._definition.namespace

    @property
    def install_location(self):
        """Return installation path.

        If a variant is used and if it defines an installation path, this value
        is returned. Otherwise, the installation path value from the initial
        definition is returned.

        :return: Directory path or None.

        """
        if self.variant is not None and self.variant.install_location:
            return self.variant.install_location
        return self._definition.install_location

    @property
    def environ(self):
        """Return environment variable mapping.

        If a variant is used and if it defines an environment variable mapping,
        this value is :func:`combined <combine_environ_mapping>` with the
        environment variable mapping defined in the initial definition.

        :return: Dictionary value.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        """
        # Create cache value if necessary.
        if self._cache.get("environ") is None:
            if self.variant is not None and len(self.variant.environ) > 0:
                self._cache["environ"] = combine_environ_mapping(
                    self.identifier,
                    self._definition.environ,
                    self.variant.environ
                )

            else:
                self._cache["environ"] = self._definition.environ

        # Return cached value.
        return self._cache.get("environ", {})

    @property
    def command(self):
        """Return command mapping.

        If a variant is used and if it defines a command mapping, this value is
        :func:`combined <combine_command_mapping>` with the command mapping
        defined in the initial definition.

        :return: Dictionary value.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        """
        # Create cache value if necessary.
        if self._cache.get("command") is None:
            if self.variant is not None and len(self.variant.command) > 0:
                self._cache["command"] = combine_command_mapping(
                    self.identifier,
                    self._definition.command,
                    self.variant.command
                )

            else:
                self._cache["command"] = self._definition.command

        # Return cached value.
        return self._cache.get("command", {})

    @property
    def requirements(self):
        """Return list of requirements.

        If a variant is used and if it defines a list of requirements, this
        value is added to the requirement list defined in the initial
        definition.

        :return: List of :class:`packaging.requirements.Requirement` instances.

        .. note::

            The value is cached when accessed once to ensure faster access
            afterwards.

        """
        # Create cache value if necessary.
        if self._cache.get("requirements") is None:
            if self.variant is not None and len(self.variant.requirements) > 0:
                self._cache["requirements"] = (
                    # To prevent mutating the the original requirement list.
                    self._definition.requirements[:]
                    + self.variant.requirements
                )
            else:
                self._cache["requirements"] = self._definition.requirements

        # Return cached value.
        return self._cache.get("requirements", [])

    @property
    def conditions(self):
        """Return list of conditions.

        :return: List of :class:`packaging.requirements.Requirement` instances.

        """
        return self._definition.conditions

    @property
    def conditions_processed(self):
        """Indicate whether the package conditions have been processed.

        :return: Boolean value.

        """
        return self._conditions_processed

    @conditions_processed.setter
    def conditions_processed(self, value):
        """Set whether the package conditions have been processed.

        :param value: Boolean value.

        """
        self._conditions_processed = value

    def localized_environ(self):
        """Return localized environ mapping.

        The :envvar:`INSTALL_ROOT` and :envvar:`INSTALL_LOCATION` values within
        the environment variable mapping will be replaced respectfully by the
        values of the :ref:`install-root <definition/install_root>` and
        :ref:`install-location <definition/install_location>` keywords.

        :return: Dictionary value.

        """
        if not self.install_location:
            return self.environ

        path = self.install_location

        if self._definition.install_root:
            path = wiz.environ.substitute(
                path, {wiz.symbol.INSTALL_ROOT: self._definition.install_root}
            )

        # Localize each environment variable.
        _environ = self.environ

        def _replace_location(mapping, item):
            """Replace install-location in *item* for *mapping*."""
            mapping[item[0]] = wiz.environ.substitute(
                item[1], {wiz.symbol.INSTALL_LOCATION: path}
            )
            return mapping

        _environ = functools.reduce(_replace_location, _environ.items(), {})
        return _environ

    def data(self):
        """Return Mapping representing the package.

        :return: Dictionary value.

        """
        data = self._definition.data()
        data["identifier"] = self.identifier

        if self.environ:
            data["environ"] = self.environ

        if self.command:
            data["command"] = self.command

        if self.install_location:
            data["install-location"] = self.install_location

        if self._variant_index is not None:
            # Remove variants from data
            variants = data.pop("variants")

            # Add variant identifier to data.
            data["variant-identifier"] = self.variant_identifier

            # Update requirements if necessary
            if len(data.get("requirements", [])):
                variant_data = variants[self._variant_index]
                data["requirements"] += variant_data.get("requirements", [])

        return data

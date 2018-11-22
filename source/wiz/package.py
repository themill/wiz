# :coding: utf-8

import mlog

import wiz.definition
import wiz.mapping
import wiz.symbol
import wiz.history
import wiz.environ
import wiz.exception


def extract(requirement, definition_mapping, namespaces=None):
    """Extract list of :class:`Package` instances from *requirement*.

    The best matching :class:`~wiz.definition.Definition` version instances
    corresponding to the *requirement* will be used.

    If this definition contains variants, a :class:`Package` instance will be
    returned for each combined variant.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available definitions
    associated with their unique identifier.

    *namespaces* could be a list which provides hints to select a default
    namespace if necessary.

    """
    definition = wiz.definition.query(
        requirement, definition_mapping, namespaces=namespaces
    )

    # Extract variants from definition if available.
    variants = definition.variants

    # Extract and return the requested variant if necessary.
    if len(requirement.extras) > 0:
        variant_identifier = next(iter(requirement.extras))
        variant_mapping = reduce(
            lambda res, mapping: dict(res, **{mapping["identifier"]: mapping}),
            variants, {}
        )

        if variant_identifier not in variant_mapping.keys():
            raise wiz.exception.RequestNotFound(
                "The variant '{variant}' could not been resolved for "
                "'{definition}' [{version}].".format(
                    variant=variant_identifier,
                    definition=definition.identifier,
                    version=definition.version
                )
            )

        return [Package(definition, variant_mapping[variant_identifier])]

    # Simply return the package corresponding to the main definition if no
    # variants are available.
    elif len(variants) == 0:
        return [Package(definition)]

    # Otherwise, extract and return all possible variants.
    else:
        return map(lambda variant: Package(definition, variant), variants)


def extract_context(packages, environ_mapping=None):
    """Return combined mapping extracted from *packages*.

    A context mapping should look as follow::

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

    *packages* should be a list of :class:`Package` instances. it should be
    ordered from the less important to the most important so that the later are
    prioritized over the first.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented.

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

    mapping = reduce(_combine, packages, dict(environ=environ_mapping or {}))
    mapping["environ"] = wiz.environ.sanitise(mapping.get("environ", {}))

    wiz.history.record_action(
        wiz.symbol.CONTEXT_EXTRACTION_ACTION,
        packages=packages, initial=environ_mapping, context=mapping
    )
    return mapping


def combine_environ_mapping(package_identifier, mapping1, mapping2):
    """Return combined environ mapping from *mapping1* and *mapping2*.

    *package_identifier* must be the identifier of the combined package. It will
    be used to indicate whether any variable is overridden in the combination
    process.

    *mapping1* and *mapping2* must be mappings of environment variables.

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

    .. warning::

        This process will stringify all variable values.

    """
    logger = mlog.Logger(__name__ + ".combine_environ_mapping")

    mapping = {}

    for key in set(mapping1.keys() + mapping2.keys()):
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

    *package_identifier* must be the identifier of the combined package. It will
    be used to indicate whether any variable is overridden in the combination
    process.

    *mapping1* and *mapping2* must be mappings of commands.

    If the command exists in both mappings, the value from *mapping2* will have
    priority over elements from *mapping1*::

        >>> combine_command_mapping(
        ...     "combined_package",
        ...     {"app": "App1.1 --run"},
        ...     {"app": "App2.1"}
        ... )

        {"app": "App2.1"}

    """
    logger = mlog.Logger(__name__ + ".combine_command_mapping")

    mapping = {}

    for command in set(mapping1.keys() + mapping2.keys()):
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


class Package(wiz.mapping.Mapping):
    """Package object."""

    def __init__(self, definition, variant=None):
        """Initialise Package from *definition*.

        *definition* must be a valid :class:`~wiz.definition.Definition`
        instance.

        *variant* could be a valid variant mapping which should have at least
        an 'identifier' keyword.

        .. note::

            In case of conflicted elements in 'data' or 'command' elements,
            the elements from the *variant* will have priority.

        """
        definition_data = definition.to_dict()
        mapping = dict(
            (k, v) for k, v in definition_data.items() if k != "variants"
        )

        mapping["variant_name"] = None

        if variant is not None:
            mapping["variant_name"] = variant.identifier

            mapping["environ"] = combine_environ_mapping(
                self._generate_identifier(mapping),
                definition.environ, variant.environ
            )

            mapping["command"] = combine_command_mapping(
                self._generate_identifier(mapping),
                definition.command, variant.command
            )

            if len(variant.get("requirements", [])) > 0:
                mapping["requirements"] = (
                    # To prevent mutating the the original requirement list.
                    definition_data.get("requirements", [])[:]
                    + variant["requirements"]
                )

            if len(variant.get("constraints", [])) > 0:
                mapping["constraints"] = (
                    # To prevent mutating the the original constraint list.
                    definition_data.get("constraints", [])[:]
                    + variant["constraints"]
                )

        super(Package, self).__init__(mapping)

    def _generate_identifier(self, mapping):
        """Generate package identifier."""
        identifier = mapping["identifier"]

        if mapping.get("variant_name") is not None:
            identifier += "[{}]".format(mapping.get("variant_name"))

        if mapping.get("version") is not None:
            identifier += "=={}".format(mapping.get("version"))

        return identifier

    @property
    def identifier(self):
        """Return package identifier."""
        return self._generate_identifier(self)

    @property
    def qualified_identifier(self):
        """Return qualified identifier with optional namespace."""
        if self.namespace is not None:
            return "{}::{}".format(self.namespace, self.identifier)
        return self.identifier

    @property
    def definition_identifier(self):
        """Return definition identifier."""
        return self.get("identifier")

    @property
    def variant_name(self):
        """Return variant name."""
        return self.get("variant_name")

    @property
    def _ordered_keywords(self):
        """Return ordered keywords."""
        return [
            "identifier",
            "definition-identifier",
            "variant_name",
            "version",
            "description",
            "registry",
            "definition-location",
            "install-location",
            "namespace",
            "auto-use",
            "system",
            "command",
            "environ",
            "requirements",
            "constraints"
        ]

    def localized_environ(self):
        """Return localized environ mapping."""
        _environ = self.environ

        def _replace_location(mapping, item):
            """Replace location in *item* for *mapping*."""
            mapping[item[0]] = item[1].replace(
                "${{{}}}".format(wiz.symbol.INSTALL_LOCATION),
                self.get("install-location")
            )
            return mapping

        if "install-location" in self.keys():
            _environ = reduce(_replace_location, _environ.items(), {})

        return _environ

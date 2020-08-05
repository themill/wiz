# :coding: utf-8

import wiz.definition
import wiz.environ
import wiz.exception
import wiz.history
import wiz.logging
import wiz.mapping
import wiz.symbol


def extract(requirement, definition_mapping, namespace_counter=None):
    """Extract list of :class:`Package` instances from *requirement*.

    The best matching :class:`~wiz.definition.Definition` version instances
    corresponding to the *requirement* will be used.

    If this definition contains variants, a :class:`Package` instance will be
    returned for each combined variant.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available definitions
    associated with their unique identifier.

    *namespace_counter* is an optional :class:`collections.Counter` instance
    which indicate occurrence of namespaces used as hints for package
    identification.

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
    logger = wiz.logging.Logger(__name__ + ".combine_environ_mapping")

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
    logger = wiz.logging.Logger(__name__ + ".combine_command_mapping")

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


def create(definition, variant_identifier=None):
    """Create and return a package from *definition*.

    *definition* must be a valid :class:`~wiz.definition.Definition` instance.

    *variant_identifier* could be a valid variant identifier.

    .. note::

        In case of conflicted elements in 'data' or 'command' elements, the
        elements from the variant will have priority.

    Raise :exc:`wiz.exception.RequestNotFound` if *variant_identifier* is not a
    valid variant identifier of *definition*.

    """
    mapping = definition.to_dict()

    # Set definition
    mapping["definition"] = definition

    # Update identifier.
    if variant_identifier is not None:
        mapping["identifier"] += "[{}]".format(variant_identifier)

    if mapping.get("version") is not None:
        mapping["identifier"] += "=={}".format(mapping.get("version"))

    # Extract data from variants.
    variants = mapping.pop("variants", [])

    if variant_identifier is not None:
        success = False

        for _mapping in variants:
            if variant_identifier == _mapping.get("identifier"):
                mapping["variant-name"] = variant_identifier

                if len(_mapping.get("environ", {})) > 0:
                    mapping["environ"] = combine_environ_mapping(
                        mapping["identifier"],
                        definition.environ, _mapping.environ
                    )

                if len(_mapping.get("command", {})) > 0:
                    mapping["command"] = combine_command_mapping(
                        mapping["identifier"],
                        definition.command, _mapping.command
                    )

                if len(_mapping.get("requirements", [])) > 0:
                    mapping["requirements"] = (
                        # To prevent mutating the the original requirement list.
                        mapping.get("requirements", [])[:]
                        + _mapping["requirements"]
                    )

                if _mapping.get("install-location") is not None:
                    mapping["install-location"] = _mapping["install-location"]

                success = True
                break

        if not success:
            raise wiz.exception.RequestNotFound(
                "The variant '{variant}' could not been resolved for "
                "'{definition}' [{version}].".format(
                    variant=variant_identifier,
                    definition=definition.identifier,
                    version=definition.version
                )
            )

    return Package(mapping)


class Package(wiz.mapping.Mapping):
    """Package object."""

    def __init__(self, *args, **kwargs):
        """Initialise package."""
        super(Package, self).__init__(*args, **kwargs)

    @property
    def qualified_identifier(self):
        """Return qualified identifier with optional namespace."""
        if self.namespace is not None:
            return "{}::{}".format(self.namespace, self.identifier)
        return self.identifier

    @property
    def definition(self):
        """Return :class:`wiz.definition.Definition` instance."""
        return self.get("definition")

    @property
    def variant_name(self):
        """Return variant name."""
        return self.get("variant-name")

    @property
    def _ordered_keywords(self):
        """Return ordered keywords."""
        return [
            "identifier",
            "definition",
            "variant-name",
            "version",
            "namespace",
            "description",
            "registry",
            "definition-location",
            "install-root",
            "install-location",
            "auto-use",
            "system",
            "command",
            "environ",
            "requirements",
            "conditions"
        ]

    def localized_environ(self):
        """Return localized environ mapping."""
        # Extract install location value.
        _install_location = self.get("install-location")

        if "install-root" in self.keys():
            _install_location = wiz.environ.substitute(
                self.get("install-location"),
                {wiz.symbol.INSTALL_ROOT: self.get("install-root")}
            )

        # Localize each environment variable.
        _environ = self.environ

        def _replace_location(mapping, item):
            """Replace install-location in *item* for *mapping*."""
            mapping[item[0]] = wiz.environ.substitute(
                item[1], {wiz.symbol.INSTALL_LOCATION: _install_location}
            )
            return mapping

        if "install-location" in self.keys():
            _environ = reduce(_replace_location, _environ.items(), {})

        return _environ

# :coding: utf-8

import traceback

import wiz.utility


class WizError(Exception):
    """Base class for Wiz specific errors."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        self.message = message
        self.traceback = traceback.format_exc()

    def __str__(self):
        """Return human readable representation."""
        return str(self.message)


class CurrentSystemError(WizError):
    """Raise when the system is incorrect."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(CurrentSystemError, self).__init__(message=message)


class UnsupportedPlatform(CurrentSystemError):
    """Raise when the current platform is not supported."""

    def __init__(self, platform):
        """Initialize with *platform*.

        :param platform: Lowercase name of the current platform as returned by
            :func:`platform.system`.

        """
        super(UnsupportedPlatform, self).__init__(
            message="The current platform is not supported: {}".format(platform)
        )


class RequestNotFound(WizError):
    """Raise when a request cannot be processed."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(RequestNotFound, self).__init__(message=message)


class DefinitionError(WizError):
    """Raise when a definition is incorrect."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(DefinitionError, self).__init__(message=message)


class PackageError(WizError):
    """Raise when a package is incorrect."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(PackageError, self).__init__(message=message)


class RequirementError(WizError):
    """Raise when a requirement is incorrect."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(RequirementError, self).__init__(message=message)


class VersionError(WizError):
    """Raise when a version is incorrect."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(VersionError, self).__init__(message=message)


class GraphResolutionError(WizError):
    """Raise when the graph is incorrect."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(GraphResolutionError, self).__init__(message=message)


class GraphConflictsError(GraphResolutionError):
    """Raise when unsolvable conflicts are found in the graph."""

    def __init__(self, conflicts):
        """Initialize with a list of conflict mappings.

        :param conflicts: List of conflict mappings which should be in the
            form of::

                [
                    {
                        "requirement": Requirement("foo >=0.1.0, <1"),
                        "identifiers": {"bar", "bim"},
                        "conflicts": {"baz"},
                        "graph": Graph()
                    },
                    {
                        "requirement": Requirement("foo >2"),
                        "identifiers": {"baz"},
                        "conflicts": {"bar", "bim"},
                        "graph": Graph()
                    }
                    ...
                ]

        """
        self.conflicts = conflicts

        def _format(mapping):
            """Display conflicting *mapping*."""
            identifiers = list(mapping["identifiers"])[:3]
            if len(mapping["identifiers"]) > 3:
                others = len(mapping["identifiers"]) - 3
                identifiers += ["+{} packages...".format(others)]

            return "  * {requirement} \t[{identifiers}]".format(
                requirement=mapping["requirement"],
                identifiers=", ".join(identifiers)
            )

        super(GraphConflictsError, self).__init__(
            message=(
                "The dependency graph could not be resolved due to the "
                "following requirement conflicts:\n"
                "{}\n".format("\n".join([_format(m) for m in conflicts]))
            )
        )


class GraphInvalidNodesError(GraphResolutionError):
    """Raise when invalid nodes are found in the graph."""

    def __init__(self, error_mapping):
        """Initialize with a list of conflict mappings.

        :param error_mapping: Mapping containing list of error messages per node
            identifier.

        """
        self.error_mapping = error_mapping

        super(GraphInvalidNodesError, self).__init__(
            message=(
                "The dependency graph could not be resolved due to the "
                "following error(s):\n"
                "{}\n".format(
                    "\n".join([
                        "  * {}: {}".format(identifier, error)
                        for identifier, errors in sorted(error_mapping.items())
                        for error in errors
                    ])
                )
            )
        )


class GraphVariantsError(GraphResolutionError):
    """Raise when division of the graph into new combinations in required."""

    def __init__(self):
        """Initialize Error."""
        super(GraphResolutionError, self).__init__(
            message="The current graph has conflicting variants."
        )


class FileExists(WizError):
    """Raise when a file already exists."""

    def __init__(self, path):
        """Initialize with *message*.

        :param path: File path.

        """
        super(FileExists, self).__init__(
            message="{!r} already exists.".format(path)
        )


class DefinitionsExist(WizError):
    """Raise when definitions already exists in a registry."""

    def __init__(self, definitions):
        """Initialize with list of existing *definitions*.

        :param definitions: List of :class:`wiz.definition.Definition`
            instances.

        """
        self.definitions = [
            wiz.utility.compute_label(definition)
            for definition in definitions

        ]

        super(DefinitionsExist, self).__init__(
            message="{} definition(s) already exist in registry.".format(
                len(definitions)
            )
        )


class InstallError(WizError):
    """Raise when the installation of a definition failed."""

    def __init__(self, message):
        """Initialize with *message*.

        :param message: Message describing the issue.

        """
        super(InstallError, self).__init__(message=message)


class InstallNoChanges(WizError):
    """Raise when no content was detected in a release request."""

    def __init__(self):
        """Initialize Error."""
        super(InstallNoChanges, self).__init__(message="Nothing to install.")

# :coding: utf-8

import traceback


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

    def __eq__(self, other):
        """Compare with *other*."""
        if isinstance(other, WizError):
            return self.message == other.message
        return False


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

    def __init__(self, conflicting):
        """Initialize with a list of conflict mappings.

        :param conflicting: Mapping of conflicting node identifiers per
            requirement. It should be in the form of::

                {
                    Requirement("foo >=0.1.0, <1"): {"bar", "bim"},
                    Requirement("foo >2"): {"baz},
                    ...
                }

        """
        # Sort conflicting requirements per ascending number of conflicting
        # nodes so that resolver attempts to downgrade versions of the smallest
        # cluster first.
        self.conflicts = sorted(
            conflicting.items(), key=lambda t: (len(t[1]), str(t[0]))
        )

        def _format(requirement, identifiers):
            """Display conflicting *mapping*."""
            # Convert set to list and sort to make message deterministic.
            identifiers = sorted(identifiers)

            # Truncate list if too long.
            if len(identifiers) > 3:
                _ellipsis = "+{} packages...".format(len(identifiers[3:]))
                identifiers = identifiers[:3] + [_ellipsis]

            return "  * {requirement} \t[{identifiers}]".format(
                requirement=requirement,
                identifiers=", ".join(identifiers)
            )

        super(GraphConflictsError, self).__init__(
            message=(
                "The dependency graph could not be resolved due to the "
                "following requirement conflicts:\n"
                "{}\n".format("\n".join([_format(*c) for c in self.conflicts]))
            )
        )

    def __eq__(self, other):
        """Compare with *other*."""
        if isinstance(other, GraphConflictsError):
            return self.conflicts == other.conflicts
        return super(GraphConflictsError, self).__eq__(other)


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

    def __eq__(self, other):
        """Compare with *other*."""
        if isinstance(other, GraphInvalidNodesError):
            return self.error_mapping == other.error_mapping
        return super(GraphInvalidNodesError, self).__eq__(other)


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

        :param definitions: List of definition labels (e.g. "'foo' [0.1.0]").

        """
        self.definitions = definitions

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

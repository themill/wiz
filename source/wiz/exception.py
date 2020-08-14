# :coding: utf-8

import traceback

import packaging.requirements


class WizError(Exception):
    """Base class for Wiz specific errors."""

    default_message = "Unspecified Wiz error occurred."

    def __init__(self, message=None, details=None):
        """Initialize with *message* and optional *details*.

        :param message: Message to display instead of :attr:`default_message`.
            Default is None.

        :param details: Mapping of additional contextual information. Its
            contents may be referenced in the message. Default is None.

        """
        self.message = message or self.default_message

        if details is None:
            details = {}

        self.details = {}
        for key, value in details.items():
            self.details[key] = value

        self.traceback = traceback.format_exc()

    def __str__(self):
        """Return human readable representation."""
        return str(self.message.format(**self.details))


class IncorrectSystem(WizError):
    """Raise when the system is incorrect."""

    default_message = "The current system is incorrect."


class UnsupportedPlatform(WizError):
    """Raise when the current platform is not supported."""

    default_message = "The current platform is not supported: {platform}"

    def __init__(self, platform):
        """Initialize with *platform*."""
        super(UnsupportedPlatform, self).__init__(
            details={"platform": platform}
        )


class IncorrectDefinition(WizError):
    """Raise when a definition is incorrect."""

    default_message = "The definition is incorrect."


class RequestNotFound(WizError):
    """Raise when a requirement is incorrect."""

    default_message = "The requirement could not be resolved."

    def __init__(self, message=None, details=None):
        """Initialize with *message* and optional *details*.

        :param message: Message to display instead of :attr:`default_message`,
            or instance of :class:`packaging.requirements.Requirement`. Default
            is None.

        :param details: Mapping of additional contextual information. Its
            contents may be referenced in the message. Default is None.

        """
        if isinstance(message, packaging.requirements.Requirement):
            if details is None:
                details = {}

            details.setdefault("name", str(message))
            message = "The requirement '{name}' could not be resolved."

        super(RequestNotFound, self).__init__(
            message=message, details=details
        )


class GraphResolutionError(WizError):
    """Raise when the environment graph is incorrect."""

    default_message = "The environment graph could not be resolved."

    def __init__(self, message=None, details=None, conflicts=None):
        """Initialize with *message* and optional *details*.

        :param message: Message to display instead of :attr:`default_message`.
            Default is None.

        :param details: Mapping of additional contextual information. Its
            contents may be referenced in the message. Default is None.

        :param conflicts: None or List of conflicting requirement mappings with
            corresponding parent identifiers which should be in the form of::

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
                ]

        """
        super(GraphResolutionError, self).__init__(
            message=message, details=details
        )

        # Record conflicting requirement mappings.
        self.conflicts = conflicts or []


class InvalidRequirement(WizError):
    """Raise when a requirement is incorrect."""

    default_message = "The requirement is incorrect."


class InvalidVersion(WizError):
    """Raise when a version is incorrect."""

    default_message = "The version is incorrect."


class FileExists(WizError):
    """Raise when a file already exists."""

    default_message = "The file already exists."


class DefinitionsExist(WizError):
    """Raise when definitions already exists in a registry."""

    default_message = "Definitions already exist."

    def __init__(self, definition_labels):
        """Initialize with list of existing *definitions*.

        :param definition_labels: List in the form of
            ::

                [
                    "foo",
                    "bar 0.1.0",
                    "baz [linux : el =! 7]",
                    "baz [linux : el >= 6, < 7]"
                ]

        """
        self.definitions = definition_labels

        super(DefinitionsExist, self).__init__(
            message="{} definition(s) already exist in registry.".format(
                len(definition_labels)
            )
        )


class InstallNoChanges(WizError):
    """Raise when no content was detected in a release request."""

    default_message = "Nothing to install."


class InstallError(WizError):
    """Raise when the installation of a definition failed."""

    default_message = "The definition cannot be installed."

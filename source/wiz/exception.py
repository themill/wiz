# :coding: utf-8

import sys
import traceback

import packaging.requirements


class WizError(Exception):
    """Base class for Wiz specific errors."""

    default_message = "Unspecified Wiz error occurred."

    def __init__(self, message=None, details=None):
        """Initialise with *message* and optional *details*.

        Use :attr:`default_message` if *message* not specified.

        *details* should be a mapping of additional contextual information. Its
        contents may be referenced in the message.

        """
        self.message = message or self.default_message

        if details is None:
            details = {}

        self.details = {}
        for key, value in details.iteritems():
            if isinstance(value, unicode):
                value = value.encode(sys.getfilesystemencoding())
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
        """Initialise with *platform*."""
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
        """Initialise with *message* and optional *details*.

        Use :attr:`default_message` if *message* not specified.

        Alternatively, *message* may be an instance of
        :class:`packaging.requirements.Requirement`.

        *details* should be a mapping of additional contextual information. Its
        contents may be referenced in the message.

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


class InvalidRequirement(WizError):
    """Raise when a requirement is incorrect."""

    default_message = "The requirement is incorrect."


class InvalidVersion(WizError):
    """Raise when a version is incorrect."""

    default_message = "The version is incorrect."

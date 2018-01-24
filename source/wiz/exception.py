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


class IncorrectDefinition(WizError):
    """Raise when a definition is incorrect."""

    default_message = "The definition {definition[identifier]} is incorrect."


class GraphResolutionError(WizError):
    """Raise when the definition graph is incorrect."""

    default_message = "The environment definition graph could not be resolved."


class CommandError(WizError):
    """Raise when the command requested is incorrect."""

    def __init__(self, command):
        """Initialise with *command*."""
        super(CommandError, self).__init__(
            message="The command '{name}' requested could not be found.",
            details={"name": command}
        )


class IncorrectRequirement(WizError):
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

            details.setdefault("name", message.name)
            message = "The requirement '{name}' could not be resolved."

        super(IncorrectRequirement, self).__init__(
            message=message, details=details
        )

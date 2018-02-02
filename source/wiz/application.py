# :coding: utf-8

import collections
import shlex

from packaging.requirements import Requirement, InvalidRequirement

import wiz.symbol
import wiz.exception
import wiz.environment
import wiz.spawn


def get(identifier, application_mapping):
    """Get :class:`Application` instance from *identifier*.

    *identifier* should be the reference to the application identifier required.

    *application_mapping* is a mapping regrouping all available application
    associated with their unique identifier.

    :exc:`wiz.exception.RequestNotFound` is raised if the
    identifier can not be found.

    """
    if identifier not in application_mapping:
        raise wiz.exception.RequestNotFound(
            "The application '{}' can not be found.".format(identifier)
        )

    return application_mapping[identifier]


def run(
    application, environment_mapping, arguments=None, data_mapping=None
):
    """Run *application* command.

    *application* must be valid :class:`Application` instance.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    *arguments* can be an optional list of command arguments.

    *data_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    Raise :exc:`wiz.exception.GraphResolutionError` if the environment graph
    cannot be resolved.

    """
    environments = wiz.environment.resolve(
        application.requirement, environment_mapping
    )

    environment = wiz.environment.combine(
        environments, data_mapping=data_mapping
    )

    command = application.command
    command_mapping = environment.get("command", {})
    if command in command_mapping.keys():
        command = command_mapping[command]

    commands = shlex.split(command)
    if arguments is not None:
        commands += arguments

    wiz.spawn.execute(commands, environment["data"])


class Application(collections.MutableMapping):
    """Application Definition."""

    def __init__(self, *args, **kwargs):
        """Initialise application."""
        super(Application, self).__init__()
        self._mapping = {}
        self.update(*args, **kwargs)

        try:
            self._mapping["requirement"] = map(
                Requirement, self.get("requirement", [])
            )

        except InvalidRequirement as error:
            raise wiz.exception.IncorrectApplication(
                "The application '{}' is incorrect: {}".format(
                    self.identifier, error
                )
            )

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier", "unknown")

    @property
    def type(self):
        """Return application type."""
        return wiz.symbol.APPLICATION_TYPE

    @property
    def description(self):
        """Return description."""
        return self.get("description", "unknown")

    @property
    def command(self):
        """Return command."""
        return self.get("command", "unknown")

    @property
    def requirement(self):
        """Return requirement list."""
        return self.get("requirement", [])

    def __str__(self):
        """Return string representation."""
        return "{}({!r}, {!r})".format(
            self.__class__.__name__, self.identifier, self._mapping
        )

    def __getitem__(self, key):
        """Return value for *key*."""
        return self._mapping[key]

    def __setitem__(self, key, value):
        """Set *value* for *key*."""
        self._mapping[key] = value

    def __delitem__(self, key):
        """Delete *key*."""
        del self._mapping[key]

    def __iter__(self):
        """Iterate over all keys."""
        for key in self._mapping:
            yield key

    def __len__(self):
        """Return count of keys."""
        return len(self._mapping)

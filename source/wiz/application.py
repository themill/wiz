# :coding: utf-8

import shlex

import wiz.symbol
import wiz.exception
import wiz.environment
import wiz.spawn


def get(identifier, application_mapping):
    """Get :class:`wiz.definition.Application` instance from *identifier*.

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


def resolve_environments(application, environment_mapping):
    """Return resolved environments from *application*'s requirements.

    *application* must be valid :class:`wiz.definition.Application` instance.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    Raise :exc:`wiz.exception.GraphResolutionError` if the environment graph
    cannot be resolved.

    """
    return wiz.environment.resolve(application.requirement, environment_mapping)


def extract_commands(application, environment, arguments=None):
    """Extract command list from *application*.

    *application* must be valid :class:`wiz.definition.Application` instance.

    *environment* must be valid :class:`wiz.definition.Environment` instance.

    *arguments* can be an optional list of command arguments.

    """
    command = application.command

    command_mapping = environment.get("alias", {})
    if command in command_mapping.keys():
        command = command_mapping[command]

    commands = shlex.split(command)
    if arguments is not None:
        commands += arguments

    return commands

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


def run(
    application, environment_mapping, arguments=None, data_mapping=None
):
    """Run *application* command.

    *application* must be valid :class:`wiz.definition.Application` instance.

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

    data_mapping = wiz.environment.initiate_data(data_mapping=data_mapping)
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

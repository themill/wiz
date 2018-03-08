# :coding: utf-8

from _version import __version__
import shlex

from packaging.requirements import Requirement

import wiz.definition
import wiz.environment
import wiz.symbol
import wiz.spawn


def fetch_definitions(paths, max_depth=None):
    """Return mapping from all definitions available under *paths*.

    Discover all available definitions under *paths*, searching recursively
    up to *max_depth*.

    A definition mapping should be in the form of::

        {
            "application": {
                "app": <Application(identifier="app")>,
                ...
            },
            "environment": {
                "app-env": [
                    <Environment(identifier="app-env", version="1.1.0")>,
                    <Environment(identifier="app-env", version="1.0.0")>,
                    <Environment(identifier="app-env", version="0.1.0")>,
                    ...
                ]
                ...
            }
        }

    """
    return wiz.definition.fetch(paths, max_depth=max_depth)


def resolve_environment(requirements, definition_mapping, data_mapping=None):
    """Return environment mapping from *requirements*.

    An environment mapping should be in the form of::

        {
            "alias": {
                "app": "AppExe"
                ...
            },
            "data": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            }
        }

    *requirements* should be a list of string indicating the environment version
    requested to build the environment (e.g. ["app-env >= 1.0.0, < 2"])

    *definition_mapping* is a mapping regrouping all available environment
    and application definitions available.

    *data_mapping* can be a mapping of environment variables which would
    be augmented by the resolved data environment.

    """
    requirements = map(Requirement, requirements)

    environments = wiz.environment.resolve(
        requirements, definition_mapping[wiz.symbol.ENVIRONMENT_TYPE]
    )

    _data_mapping = wiz.environment.initiate_data(data_mapping)
    return wiz.environment.combine(
        environments, data_mapping=_data_mapping
    )


def resolve_environment_data(
    requirements, definition_mapping, data_mapping=None
):
    """Return environment data mapping from *requirements*.

    An environment data mapping should be in the form of::

        {
            "KEY1": "value1",
            "KEY2": "value2",
            ...
        }

    *requirements* should be a list of string indicating the environment version
    requested to build the environment (e.g. "app-env >= 1.0.0, < 2")

    *definition_mapping* is a mapping regrouping all available environment
    and application definitions available.

    *data_mapping* can be a mapping of environment variables which would
    be augmented by the resolved data environment.

    """
    _environment = resolve_environment(
        requirements, definition_mapping, data_mapping
    )
    return _environment.get("data", {})


def execute(command, requirements, definition_mapping, data_mapping=None):
    """Execute *command* within resolved environment from *requirements*.

    *command* should be a string representing an executable with possible
    arguments that could be run within the resolved environment. The executable
    could be an alias available within the resolved environment.

    *requirements* should be a list of string indicating the environment version
    requested to build the environment (e.g. "app-env >= 1.0.0, < 2")

    *definition_mapping* is a mapping regrouping all available environment
    and application definitions available.

    *data_mapping* can be a mapping of environment variables which would
    be augmented by the resolved data environment.

    """
    commands = shlex.split(command)

    _environment = resolve_environment(
        requirements, definition_mapping, data_mapping
    )

    alias_mapping = _environment.get("alias", {})
    if commands[0] in alias_mapping.keys():
        commands = shlex.split(alias_mapping[commands[0]]) + commands[1:]

    wiz.spawn.execute(commands, _environment.get("data", {}))

# :coding: utf-8

import shlex

from packaging.requirements import Requirement

from _version import __version__
import wiz.definition
import wiz.package
import wiz.graph
import wiz.symbol
import wiz.spawn
import wiz.system


def fetch_definitions(paths, max_depth=None, system_mapping=None):
    """Return mapping from all definitions available under *paths*.

    Discover all available definitions under *paths*, searching recursively
    up to *max_depth*.

    definition are :class:`wiz.definition.Definition` instances.

    A definition mapping should be in the form of::

        {
            "command": {
                "app": "my-app",
                ...
            },
            "package": {
                "my-app": {
                    "1.1.0": <Definition(identifier="my-app", version="1.1.0")>,
                    "1.0.0": <Definition(identifier="my-app", version="1.0.0")>,
                    "0.1.0": <Definition(identifier="my-app", version="0.1.0")>,
                    ...
                },
                ...
            }
        }

    *system_mapping* could be a mapping of the current system. By default, the
    current system mapping will be :func:`queried <wiz.system.query>`.

    """
    if system_mapping is None:
        system_mapping = wiz.system.query()

    return wiz.definition.fetch(
        paths, system_mapping=system_mapping, max_depth=max_depth
    )


def resolve_package_context(requests, definition_mapping, environ_mapping=None):
    """Return package context mapping from *requests*.

    The context should contain the resolved environment mapping, the
    resolved command mapping, and an ordered list of all serialized packages
    which constitute the resolved context.

    It should be in the form of::

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
            "packages": [
                {"identifier": "test1==1.1.0", "version": "1.1.0", ...},
                {"identifier": "test2==0.3.0", "version": "0.3.0", ...},
                ...
            ]
        }

    *requests* should be a list of string indicating the package version
    requested to build the context (e.g. ["package >= 1.0.0, < 2"])

    *definition_mapping* is a mapping regrouping all available definitions
    available.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    requirements = map(Requirement, requests)

    resolver = wiz.graph.Resolver(
        definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )
    packages = resolver.compute_packages(requirements)

    _environ_mapping = wiz.package.initiate_environ(environ_mapping)
    context = wiz.package.extract_context(
        packages, environ_mapping=_environ_mapping
    )

    context["packages"] = packages
    return context


def resolve_command_context(request, definition_mapping, arguments=None):
    """Return command context mapping from *request*.

    The package request is extracted from the *command_request* so that the
    corresponding package context can be
    :func:`resolved <resolve_package_context>`. The resolved command is then
    computed with the *arguments* and added to the context.

    It should be in the form of::

        {
            "resolved_command": "appExe --option value /path/to/script",
            "command": {
                "app": "AppExe"
                ...
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            },
            "packages": [
                {"identifier": "test1==1.1.0", "version": "1.1.0", ...},
                {"identifier": "test2==0.3.0", "version": "0.3.0", ...},
                ...
            ]
        }

    *request* should be a string indicating the command version requested to
    build the context (e.g. ["app >= 1.0.0, < 2"]).

    *definition_mapping* is a mapping regrouping all available definitions
    available.

    *arguments* could be a list of all arguments which constitute the resolved
    command (e.g. ["--option", "value", "/path/to/script"]).

    """
    requirement = Requirement(request)

    command = requirement.name
    if arguments is not None:
        command += " ".join(arguments)

    definition_requirement = Requirement(
        definition_mapping[wiz.symbol.COMMAND_REQUEST_TYPE][requirement.name]
    )
    definition_requirement.specifier = requirement.specifier
    definition_requirement.extras = requirement.extras
    package_requests = [str(definition_requirement)]

    context = wiz.resolve_package_context(package_requests, definition_mapping)
    context["resolved_command"] = resolve_command(
        command, context.get("command")
    )
    return context


def resolve_command(command, command_mapping):
    """Return resolved command from *command* and *command_mapping*.

    *command* should be a command line in the form off::

        app_exe
        app_exe --option value
        app_exe --option value /path/to/script

    *command_mapping* should associate command aliases to real command.

    Example::

        >>> resolve_command(
        ...     "app --option value /path/to/script",
        ...     {"app": "App0.1 --modeX"}
        ... )

        "App0.1 --modeX --option value /path/to/script"

    """
    commands = shlex.split(command)

    if commands[0] in command_mapping.keys():
        commands = (
            shlex.split(command_mapping[commands[0]]) + commands[1:]
        )

    return " ".join(commands)

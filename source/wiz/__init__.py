# :coding: utf-8

import shlex
import os

from packaging.requirements import Requirement

from _version import __version__
import wiz.definition
import wiz.package
import wiz.graph
import wiz.symbol
import wiz.spawn
import wiz.system
import wiz.filesystem
import wiz.utility
import wiz.exception


def fetch_definition_mapping(paths, max_depth=None, system_mapping=None):
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
            },
            "registries": [
                ...
            ]
        }

    *system_mapping* could be a mapping of the current system. By default, the
    current system mapping will be :func:`queried <wiz.system.query>`.

    """
    if system_mapping is None:
        system_mapping = wiz.system.query()

    mapping = wiz.definition.fetch(
        paths, system_mapping=system_mapping, max_depth=max_depth
    )

    mapping["registries"] = paths
    return mapping


def fetch_definition(request, definition_mapping):
    """Return :class:`~wiz.definition.Definition` instance from request.

    *request* should be a string indicating the definition requested
    (e.g. "definition" or "definition >= 1.0.0, < 2").

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    Raises :exc:`wiz.exception.RequestNotFound` is the corresponding definition
    cannot be found.

    """
    requirement = Requirement(request)
    return wiz.definition.query(
        requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )


def fetch_definition_from_command(command_request, definition_mapping):
    """Return :class:`~wiz.definition.Definition` instance from command request.

    *command_request* should be a string indicating the command requested
    (e.g. "command" or "command >= 1.0.0, < 2").

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    Raises :exc:`wiz.exception.RequestNotFound` is the corresponding definition
    cannot be found.

    """
    requirement = Requirement(command_request)
    request_type = wiz.symbol.COMMAND_REQUEST_TYPE

    if requirement.name not in definition_mapping[request_type]:
        raise wiz.exception.RequestNotFound(
            "No command named '{}' can be found.".format(requirement.name)
        )

    _requirement = Requirement(
        definition_mapping[request_type][requirement.name]
    )
    _requirement.specifier = requirement.specifier
    return wiz.definition.query(
        _requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )


def fetch_package(request, definition_mapping):
    """Return best matching :class:`~wiz.package.Package` instance from request.

    If several packages are extracted from *request*, only the first one will be
    returned.

    *request* should be a string indicating the package requested
    (e.g. "package" or "package[Variant] >= 1.0.0, < 2").

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    Raises :exc:`wiz.exception.RequestNotFound` is the corresponding definition
    cannot be found.

    """
    packages = wiz.package.extract(request, definition_mapping)
    return packages[0]


def fetch_package_from_command(command_request, definition_mapping):
    """Return best matching :class:`~wiz.package.Package` instance from request.

    If several packages are extracted from *request*, only the first one will be
    returned.

    *command_request* should be a string indicating the command requested
    (e.g. "command" or "command >= 1.0.0, < 2").

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    Raises :exc:`wiz.exception.RequestNotFound` is the corresponding definition
    cannot be found.

    """
    requirement = Requirement(command_request)
    request_type = wiz.symbol.COMMAND_REQUEST_TYPE

    if requirement.name not in definition_mapping[request_type]:
        raise wiz.exception.RequestNotFound(
            "No command named '{}' can be found.".format(requirement.name)
        )

    _requirement = Requirement(
        definition_mapping[request_type][requirement.name]
    )
    _requirement.specifier = requirement.specifier
    _requirement.extras = requirement.extras

    return wiz.definition.query(
        _requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )


def resolve_context(requests, definition_mapping, environ_mapping=None):
    """Return context mapping from *requests*.

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
                Package(identifier="test1==1.1.0", version="1.1.0"),
                Package(identifier="test2==0.3.0", version="0.3.0"),
                ...
            ],
            "registries": [
                ...
            ]
        }

    *requests* should be a list of string indicating the package version
    requested to build the context (e.g. ["package >= 1.0.0, < 2"])

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    requirements = map(Requirement, requests)

    registries = definition_mapping["registries"]
    resolver = wiz.graph.Resolver(
        definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )
    packages = resolver.compute_packages(requirements)

    _environ_mapping = wiz.package.initiate_environ(environ_mapping)
    context = wiz.package.extract_context(
        packages, environ_mapping=_environ_mapping
    )

    context["packages"] = packages
    context["registries"] = registries

    # Augment context environment with wiz signature
    context["environ"].update({
        "WIZ_VERSION": __version__,
        "WIZ_CONTEXT": wiz.utility.encode([
            [_package.identifier for _package in packages], registries
        ])
    })
    return context


def resolve_context_from_command(
    command_request, definition_mapping, arguments=None
):
    """Return context mapping from request.

    The package request is extracted from the *command_request* so that the
    corresponding package context can be :func:`resolved <resolve_context>`.
    The resolved command is then computed with the *arguments* and added to the
    context.

    It should be in the form of::

        {
            "resolved_command": "AppExe --option value /path/to/script",
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
            ],
            "registries": [
                ...
            ]
        }

    *request* should be a string indicating the command version requested to
    build the context (e.g. ["app >= 1.0.0, < 2"]).

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    *arguments* could be a list of all arguments which constitute the resolved
    command (e.g. ["--option", "value", "/path/to/script"]).

    """
    requirement = Requirement(command_request)

    command = requirement.name
    if arguments is not None:
        command += " ".join(arguments)

    definition_requirement = Requirement(
        definition_mapping[wiz.symbol.COMMAND_REQUEST_TYPE][requirement.name]
    )
    definition_requirement.specifier = requirement.specifier
    definition_requirement.extras = requirement.extras
    package_requests = [str(definition_requirement)]

    context = wiz.resolve_context(package_requests, definition_mapping)
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


def query_context():
    """Return context mapping used to resolve the current wiz environment.

    It should be in the form of::

        {
            "packages": [
                Package(identifier="test1==1.1.0", version="1.1.0"),
                Package(identifier="test2==0.3.0", version="0.3.0"),
                ...
            ],
            "registries": [
                ...
            ]
        }

    The context should have been encoded into a :envvar:`WIZ_CONTEXT`
    environment variable that can be used to retrieve the list of registries and
    packages from which the current environment was resolved.

    .. warning::

        The context cannot be retrieved if this function is called
        outside of a environment resolved with Wiz.

    :exc:`~wiz.exception.RequestNotFound` is raised if the
    :envvar:`WIZ_CONTEXT` is not found.

    """
    encoded_context = os.environ.get("WIZ_CONTEXT")
    if encoded_context is None:
        raise wiz.exception.RequestNotFound(
            "Impossible to retrieve the current context as the 'WIZ_CONTEXT' "
            "environment variable is not set. Are you sure you are currently "
            "in a resolved environment?"
        )

    package_identifiers, registries = wiz.utility.decode(encoded_context)

    # Build definition requirements from package identifiers
    requirements = [
        Requirement(identifier) for identifier in package_identifiers
    ]

    # Extract and return each unique package from definition requirements.
    definition_mapping = wiz.fetch_definition_mapping(registries)
    packages = [
        wiz.package.extract(requirement, definition_mapping)[0]
        for requirement in requirements
    ]

    return {
        "registries": registries,
        "packages": packages
    }


def export_definition(
    path, identifier, description, version=None, command_mapping=None,
    environ_mapping=None, packages=None,
):
    """Export a context as a definition in *path*.

    It could be used as follow::

        >>> mapping = wiz.fetch_definition_mapping("/path/to/registry")
        >>> context = wiz.resolve_context(
        ...     ["my-package >=1, <2"], mapping
        ... )
        >>> wiz.export_definition(
        ...    "/path/to/output", "new-definition",
        ...    "Exported definition from 'my-package'.",
        ...    command_mapping=context.get("command"),
        ...    environ_mapping=context.get("environ")
        ... )

        "/path/to/output/new-definition.json"

    *path* should be a valid directory to save the exported definition.

    *identifier* should be a unique identifier for the exported definition.

    *description* should be a short description for the exported definition.

    *version* could be a valid version string for the exported definition. If
    unspecified the definition will be un-versioned.

    *command_mapping* could be a mapping of commands available in the exported
    definition. Each command key should be unique in a registry. The mapping
    should be in the form of::

        {
            "app": "AppExe",
            "appX": "AppExe --mode X"
        }

    *environ_mapping* could be a mapping of all environment variable that will
    be set by the exported definition. It should be in the form of::

        {
            "KEY1": "value1",
            "KEY2": "value2",
        }

    *packages* could be a list of :class:`wiz.package.Package` instances
    requested by the exported definition.

    Raises :exc:`wiz.exception.IncorrectDefinition` if the definition can not
    be created from incoming data.

    Raises :exc:`OSError` if the definition can not be exported in *path*.

    """
    definition_data = {
        "identifier": identifier,
        "description": description,
    }

    if version is not None:
        definition_data["version"] = version

    if command_mapping is not None:
        definition_data["command"] = command_mapping

    if environ_mapping is not None:
        definition_data["environ"] = environ_mapping

    if packages is not None:
        definition_data["requirements"] = [
            _package.identifier for _package in packages
        ]

    return wiz.definition.export(path, definition_data)


def export_bash_wrapper(
    path, identifier, command=None, environ_mapping=None, packages=None,
):
    """Export context as :term:`Bash` wrapper in *path*.

    Return the path to the bash wrapper created.

    *path* should be a valid directory to save the exported wrapper.

    *identifier* should define the name of the exported wrapper.

    *command* could define a command to run within the exported wrapper.

    *environ_mapping* could be a mapping of all environment variable that will
    be set by the exported definition. It should be in the form of::

        {
            "KEY1": "value1",
            "KEY2": "value2",
        }

    *packages* could indicate a list of :class:`wiz.package.Package` instances
    which helped creating the context.

    Raises :exc:`OSError` if the wrapper can not be exported in *path*.

    """
    file_path = os.path.join(os.path.abspath(path), identifier)

    content = "#!/bin/bash\n"

    # Indicate information about the generation process.
    if packages is not None:
        content += "#\n# Generated by wiz with the following environments:\n"
        for _package in packages:
            content += "# - {}\n".format(_package.identifier)
        content += "#\n"

    for key, value in environ_mapping.items():
        # Do not override the PATH environment variable to prevent
        # error when executing the script.
        if key == "PATH":
            value += ":${PATH}"

        content += "export {0}=\"{1}\"\n".format(key, value)

    if command:
        content += command + " $@"

    wiz.filesystem.export(file_path, content)
    return file_path


def export_csh_wrapper(
    path, identifier, command=None, environ_mapping=None, packages=None,
):
    """Export context as :term:`C-Shell` wrapper in *path*.

    Return the path to the bash wrapper created.

    *path* should be a valid directory to save the exported wrapper.

    *identifier* should define the name of the exported wrapper.

    *command* could define a command to run within the exported wrapper.

    *environ_mapping* could be a mapping of all environment variable that will
    be set by the exported definition. It should be in the form of::

        {
            "KEY1": "value1",
            "KEY2": "value2",
        }

    *packages* could indicate a list of :class:`wiz.package.Package` instances
    which helped creating the context.

    Raises :exc:`OSError` if the wrapper can not be exported in *path*.

    """
    file_path = os.path.join(os.path.abspath(path), identifier)

    content = "#!/bin/tcsh -f\n"

    # Indicate information about the generation process.
    if packages is not None:
        content += "#\n# Generated by wiz with the following environments:\n"
        for _package in packages:
            content += "# - {}\n".format(_package.identifier)
        content += "#\n"

    for key, value in environ_mapping.items():
        # Do not override the PATH environment variable to prevent
        # error when executing the script.
        if key == "PATH":
            value += ":${PATH}"

        content += "setenv {0} \"{1}\"\n".format(key, value)

    if command:
        content += command + " $argv:q"

    wiz.filesystem.export(file_path, content)
    return file_path

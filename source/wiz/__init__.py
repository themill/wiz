# :coding: utf-8

import shlex
import os

from _version import __version__
import wiz.registry
import wiz.definition
import wiz.package
import wiz.environ
import wiz.graph
import wiz.symbol
import wiz.spawn
import wiz.system
import wiz.filesystem
import wiz.exception
import wiz.utility


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
                    "1.1.0": Definition(identifier="my-app", version="1.1.0"),
                    "1.0.0": Definition(identifier="my-app", version="1.0.0"),
                    "0.1.0": Definition(identifier="my-app", version="0.1.0"),
                    ...
                },
                ...
            },
            "implicit-packages": [
                "foo==0.1.0", ...
            ]
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
    requirement = wiz.utility.get_requirement(request)
    return wiz.definition.query(
        requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
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
    requirement = wiz.utility.get_requirement(request)
    packages = wiz.package.extract(
        requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )
    return packages[0]


def fetch_package_request_from_command(command_request, definition_mapping):
    """Return package request corresponding to command request.

    Example::

        >>> definition_mapping = {
        ...     "command": {"hiero": "nuke"},
        ...     "package": {"nuke": ...}
        ... }
        >>> fetch_package_request_from_command(
        ...     "hiero==10.5.*", definition_mapping
        ... )
        nuke==10.5.*

    *command_request* should be a string indicating the command requested
    (e.g. "command" or "command >= 1.0.0, < 2").

    *definition_mapping* is a mapping regrouping all available definitions
    available. It could be fetched with :func:`fetch_definition_mapping`.

    Raises :exc:`wiz.exception.RequestNotFound` is the command cannot be found.

    """
    requirement = wiz.utility.get_requirement(command_request)
    request_type = wiz.symbol.COMMAND_REQUEST_TYPE

    if requirement.name not in definition_mapping[request_type]:
        raise wiz.exception.RequestNotFound(
            "No command named '{}' can be found.".format(requirement.name)
        )

    _requirement = wiz.utility.get_requirement(
        definition_mapping[request_type][requirement.name]
    )
    _requirement.specifier = requirement.specifier
    _requirement.extras = requirement.extras
    return str(_requirement)


def resolve_context(
    requests, definition_mapping=None, ignore_implicit=False,
    environ_mapping=None, timeout=300
):
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
    If no definition mapping is provided, a sensible one will be fetched from
    :func:`default registries <wiz.registry.get_defaults>`.

    *ignore_implicit* indicates whether implicit packages should not be
    included in context. Default is False.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    *timeout* is the max time to expire before the resolve process is being
    cancelled (in seconds). Default is 5 minutes.

    Raises :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
    resolved in time.

    """
    # To prevent mutating input list.
    _requests = requests[:]

    if definition_mapping is None:
        definition_mapping = wiz.fetch_definition_mapping(
            wiz.registry.get_defaults()
        )

    if not ignore_implicit:
        _requests += definition_mapping.get(wiz.symbol.IMPLICIT_PACKAGE, [])

    requirements = map(wiz.utility.get_requirement, _requests)

    registries = definition_mapping["registries"]
    resolver = wiz.graph.Resolver(
        definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE], timeout
    )
    packages = resolver.compute_packages(requirements)

    _environ_mapping = wiz.environ.initiate(environ_mapping)
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


def resolve_command(elements, command_mapping):
    """Return resolved command elements from *elements* and *command_mapping*.

    *elements* should include all command line elements in the form off::

        ["app_exe"]
        ["app_exe", "--option", "value"]
        ["app_exe", "--option", "value", "/path/to/script"]

    *command_mapping* should associate command aliases to real command.

    Example::

        >>> resolve_command(
        ...     ["app", "--option", "value", "/path/to/script"],
        ...     {"app": "App0.1 --modeX"}
        ... )

        ["App0.1", "--modeX", "--option", "value", "/path/to/script"]

    """
    if elements[0] in command_mapping.keys():
        elements = shlex.split(command_mapping[elements[0]]) + elements[1:]

    return elements


def discover_context():
    """Return context mapping used to resolve the current wiz environment.

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

    The context should have been encoded into a :envvar:`WIZ_CONTEXT`
    environment variable that can be used to retrieve the list of registries and
    packages from which the current environment was resolved.

    .. warning::

        The context cannot be retrieved if this function is called
        outside of a resolved environment.

    :exc:`~wiz.exception.RequestNotFound` is raised if the
    :envvar:`WIZ_CONTEXT` environment variable is not found.

    """
    encoded_context = os.environ.get("WIZ_CONTEXT")
    if encoded_context is None:
        raise wiz.exception.RequestNotFound(
            "Impossible to retrieve the current context as the 'WIZ_CONTEXT' "
            "environment variable is not set. Are you sure you are currently "
            "in a resolved environment?"
        )

    package_identifiers, registries = wiz.utility.decode(encoded_context)

    # Extract and return each unique package from definition requirements.
    definition_mapping = wiz.fetch_definition_mapping(registries)
    packages = [
        wiz.fetch_package(identifier, definition_mapping)
        for identifier in package_identifiers
    ]

    _environ_mapping = wiz.environ.initiate()
    context = wiz.package.extract_context(
        packages, environ_mapping=_environ_mapping
    )

    context["packages"] = packages
    context["registries"] = registries
    return context


def load_definition(path):
    """Return :class:`~wiz.definition.Definition` instance from file *path*.

    *path* should be a valid :term:`JSON` file path which contains a definition.

    A :exc:`wiz.exception.IncorrectDefinition` exception will be raised
    if the definition is incorrect.

    """
    return wiz.definition.load(path)


def export_definition(path, data, overwrite=False):
    """Export definition *data* as a :term:`JSON` file in directory *path*.

    *path* should be a valid directory to save the exported definition.

    *data* could be an instance of :class:`wiz.definition.Definition` or
    a mapping in the form of::

        {
            "identifier": "foo",
            "description": "This is my package",
            "version": "0.1.0",
            "command": {
                "app": "AppExe",
                "appX": "AppExe --mode X"
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2"
            },
            "requirements": [
                "package1 >=1, <2",
                "package2"
            ]
        }

    *overwrite* indicate whether existing definitions in the target path
    will be overwritten. Default is False.

    Raises :exc:`wiz.exception.IncorrectDefinition` if *data* is a mapping that
    cannot create a valid instance of :class:`wiz.definition.Definition`.

    Raises :exc:`wiz.exception.FileExists` if definition already exists in
    *path* and overwrite is False.

    Raises :exc:`OSError` if the definition can not be exported in *path*.

    The command identifier must also be unique in the registry.

    """
    return wiz.definition.export(path, data, overwrite=overwrite)


def install_definitions(paths, registry_target, overwrite=False):
    """Install a definition file to a registry.

    *paths* is the path list to all definition files.

    *registry_target* should be a valid :term:`VCS` registry URI or a path to a
    local registry.

    If *overwrite* is True, any existing definitions in the target registry
    will be overwritten.

    Raises :exc:`wiz.exception.IncorrectDefinition` if data in *paths* cannot
    create a valid instance of :class:`wiz.definition.Definition`.

    Raises :exc:`wiz.exception.DefinitionExists` if definition already exists in
    the target registry and *overwrite* is False.

    Raises :exc:`OSError` if the definition can not be exported in a registry
    local *path*.

    """
    definitions = []

    for path in paths:
        _definition = wiz.load_definition(path)
        definitions.append(_definition)

    if registry_target.startswith(wiz.registry.SCHEME):
        wiz.registry.install_to_vcs(
            definitions, registry_target, overwrite=overwrite
        )

    else:
        wiz.registry.install_to_path(
            definitions, registry_target, overwrite=overwrite
        )


def export_script(
    path, script_type, identifier, environ, command=None, packages=None,
):
    """Export context as :term:`Bash` wrapper in *path*.

    Return the path to the bash wrapper created.

    *path* should be a valid directory to save the exported wrapper.

    *script_type* should be either "tcsh" or "bash".

    *identifier* should define the name of the exported wrapper.

    *environ* should be a mapping of all environment variable that will
    be set by the exported definition. It should be in the form of::

        {
            "KEY1": "value1",
            "KEY2": "value2",
        }

    *command* could define a command to run within the exported wrapper.

    *packages* could indicate a list of :class:`wiz.package.Package` instances
    which helped creating the context.

    Raises :exc:`ValueError` if the *script_type* is incorrect.

    Raises :exc:`ValueError` if *environ* mapping is empty.

    Raises :exc:`OSError` if the wrapper can not be exported in *path*.

    """
    file_path = os.path.join(os.path.abspath(path), identifier)

    if script_type == "bash":
        content = "#!/bin/bash\n"
    elif script_type == "tcsh":
        content = "#!/bin/tcsh -f\n"
    else:
        raise ValueError("'{}' is not a valid script type.".format(script_type))

    # Indicate information about the generation process.
    if packages is not None:
        content += "#\n# Generated by wiz with the following environments:\n"
        for _package in packages:
            content += "# - {}\n".format(_package.identifier)
        content += "#\n"

    if len(environ.keys()) == 0:
        raise ValueError("The environment mapping should not be empty.")

    for key, value in environ.items():
        # Do not override the PATH environment variable to prevent
        # error when executing the script.
        if key == "PATH":
            value += ":${PATH}"

        if script_type == "bash":
            content += "export {0}=\"{1}\"\n".format(key, value)
        else:
            content += "setenv {0} \"{1}\"\n".format(key, value)

    if command is not None:
        if script_type == "bash":
            content += command + " $@\n"
        else:
            content += command + " $argv:q\n"

    wiz.filesystem.export(file_path, content)
    return file_path

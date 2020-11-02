# :coding: utf-8

import os
import shlex

import wiz.definition
import wiz.environ
import wiz.exception
import wiz.filesystem
import wiz.graph
import wiz.package
import wiz.registry
import wiz.spawn
import wiz.symbol
import wiz.system
import wiz.utility
from ._version import __version__


def fetch_definition_mapping(paths, max_depth=None, system_mapping=None):
    """Return mapping including all definitions available under *paths*.

    Mapping returned should be in the form of::

        {
            "command": {
                "foo-app": "foo",
                ...
            },
            "package": {
                "foo": {
                    "1.1.0": Definition(identifier="foo", version="1.1.0"),
                    "1.0.0": Definition(identifier="foo", version="1.0.0"),
                    "0.1.0": Definition(identifier="foo", version="0.1.0"),
                    ...
                },
                ...
            },
            "implicit-packages": [
                "bar==0.1.0",
                ...
            ]
            "registries": [
                "/path/to/registry",
                ...
            ]
        }

    :param paths: List of registry paths to recursively fetch
        :class:`definitions <wiz.definition.Definition>` from.

    :param max_depth: Limited recursion value to search for :class:`definitions
        <wiz.definition.Definition>`. Default is None, which means that all
        sub-trees will be visited.

    :param system_mapping: Mapping defining the current system to filter
        out non compatible definitions. Default is None, which means that the
        current system mapping will be :func:`queried <wiz.system.query>`.

    :return: Definition mapping.

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

    :param request: String indicating which definition should be fetched.
        (e.g. "definition", "definition >= 1.0.0, < 2", etc.).

    :param definition_mapping: Mapping regrouping all available definitions. It
        could be fetched with :func:`fetch_definition_mapping`.

    :return: Instance of :class:`~wiz.definition.Definition`.

    :raise: :exc:`wiz.exception.RequestNotFound` is the corresponding definition
        cannot be found.

    """
    requirement = wiz.utility.get_requirement(request)
    return wiz.definition.query(
        requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )


def fetch_package(request, definition_mapping):
    """Return best matching :class:`~wiz.package.Package` instance from request.

    :param request: String indicating which package should be fetched.
        (e.g. "package", "package[Variant] >= 1.0.0, < 2", etc.).

    :param definition_mapping: Mapping regrouping all available definitions. It
        could be fetched with :func:`fetch_definition_mapping`.

    :return: Instance of :class:`~wiz.package.Package`.

    :raise: :exc:`wiz.exception.RequestNotFound` is the corresponding definition
        cannot be found.

    .. note::

        If several packages are extracted from *request*, only the first one
        will be returned.

    """
    requirement = wiz.utility.get_requirement(request)
    packages = wiz.package.extract(
        requirement, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )
    return packages[0]


def fetch_package_request_from_command(command_request, definition_mapping):
    """Return package request corresponding to command request.

    Example::

        >>> mapping = {
        ...     "command": {"hiero": "nuke"},
        ...     "package": {"nuke": ...}
        ... }
        >>> fetch_package_request_from_command("hiero==10.5.*", mapping)
        nuke==10.5.*

    :param command_request: String indicating which command should be fetched.
        (e.g. "command", "command >= 1.0.0, < 2", etc.).

    :param definition_mapping: Mapping regrouping all available definitions. It
        could be fetched with :func:`fetch_definition_mapping`.

    :return: Package requests string.

    :raise: :exc:`wiz.exception.RequestNotFound` is the corresponding command
        cannot be found.

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
    environ_mapping=None, maximum_combinations=None, maximum_attempts=None
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
                "/path/to/registry",
                ...
            ]
        }

    :param requests: List of strings indicating the package version requested to
        build the context (e.g. ["package >= 1.0.0, < 2"])

    :param definition_mapping: Mapping regrouping all available definitions. It
        could be fetched with :func:`fetch_definition_mapping`. If no definition
        mapping is provided, a default one will be fetched from
        :func:`default registries <wiz.registry.get_defaults>`.

    :param ignore_implicit: Indicates whether implicit packages should not be
        included in context. Default is False.

    :param environ_mapping: Mapping of environment variables which would be
        augmented by the resolved environment. Default is None.

    :param maximum_combinations: Maximum number of combinations which can be
        generated from conflicting variants. Default is None, which means
        that the default value will be picked from the :ref:`configuration
        <configuration>`.

    :param maximum_attempts: Maximum number of resolution attempts before
        raising an error. Default is None, which means  that the default
        value will be picked from the :ref:`configuration <configuration>`.

    :return: Context mapping.

    :raise: :exc:`wiz.exception.GraphResolutionError` if the resolution graph
        cannot be resolved in time.

    """
    requirements = wiz.utility.get_requirements(requests)

    # Extract definition mapping from default registry paths if necessary.
    if definition_mapping is None:
        definition_mapping = wiz.fetch_definition_mapping(
            wiz.registry.get_defaults()
        )

    # Extract initial namespace counter from explicit requirements.
    namespace_counter = wiz.utility.compute_namespace_counter(
        requirements, definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )

    # Prepend implicit requests to explicit ones if necessary.
    if not ignore_implicit:
        _requests = definition_mapping.get(wiz.symbol.IMPLICIT_PACKAGE, [])
        requirements = wiz.utility.get_requirements(_requests) + requirements

    resolver = wiz.graph.Resolver(
        definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE],
        maximum_combinations=maximum_combinations,
        maximum_attempts=maximum_attempts,
    )
    packages = resolver.compute_packages(
        requirements, namespace_counter=namespace_counter
    )

    _environ_mapping = wiz.environ.initiate(environ_mapping)
    context = wiz.package.extract_context(
        packages, environ_mapping=_environ_mapping
    )

    context["packages"] = packages
    context["registries"] = definition_mapping["registries"]

    # Augment context environment with wiz signature
    context["environ"].update({
        "WIZ_VERSION": __version__,
        "WIZ_CONTEXT": wiz.utility.encode([
            [_package.identifier for _package in packages],
            definition_mapping["registries"]
        ])
    })
    return context


def resolve_command(elements, command_mapping):
    """Return resolved command elements from *elements* and *command_mapping*.

    Example::

        >>> resolve_command(
        ...     ["app", "--option", "value", "/path/to/script"],
        ...     {"app": "App0.1 --modeX"}
        ... )

        ["App0.1", "--modeX", "--option", "value", "/path/to/script"]

    :param elements: List of strings constituting the command line to resolve
        (e.g. ["app_exe", "--option", "value"])

    :param command_mapping: Mapping associating command aliased to real
        commands.

    :return: List of strings constituting the resolved command line.

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
                "/path/to/registry",
                ...
            ]
        }

    The context should have been encoded into a :envvar:`WIZ_CONTEXT`
    environment variable that can be used to retrieve the list of registries and
    packages from which the current environment was resolved.

    .. warning::

        The context cannot be retrieved if this function is called
        outside of a resolved environment.

    :return: Context mapping.

    :raise: :exc:`~wiz.exception.RequestNotFound` if the :envvar:`WIZ_CONTEXT`
        environment variable is not found.

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

    :param path: :term:`JSON` file path which contains a definition.

    :raise: :exc:`wiz.exception.IncorrectDefinition` if the definition is
        incorrect.

    """
    return wiz.definition.load(path)


def export_definition(path, data, overwrite=False):
    """Export definition *data* as a :term:`JSON` file in directory *path*.

    :param path: Target path to save the exported definition into.

    :param data: Instance of :class:`wiz.definition.Definition` or a mapping in
        the form of::

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

    :param overwrite: Indicate whether existing definitions in the target path
        will be overwritten. Default is False.

    :return: Path to exported definition.

    :raise: :exc:`wiz.exception.IncorrectDefinition` if *data* is a mapping that
        cannot create a valid instance of :class:`wiz.definition.Definition`.

    :raise: :exc:`wiz.exception.FileExists` if definition already exists in
        *path* and overwrite is False.

    :raise: :exc:`OSError` if the definition can not be exported in *path*.

    .. warning::

        Ensure that the *data* :ref:`identifier <definition/identifier>`,
        :ref:`namespace <definition/namespace>`, :ref:`version
        <definition/version>` and :ref:`system requirement <definition/system>`
        are unique in the registry.

        Each :ref:`command <definition/command>` must also be unique in the
        registry.

    """
    return wiz.definition.export(path, data, overwrite=overwrite)


def export_script(
    path, script_type, identifier, environ, command=None, packages=None,
):
    """Export environment as :term:`Bash` or :term:`C-Shell` script in *path*.

    :param path: Target path to save the exported script into.

    :param script_type: Should be either :term:`tcsh <C-Shell>` or
        :term:`bash <Bash>`.

    :param identifier: File name of the exported script.

    :param environ: Mapping of all environment variables that will be set by the
        exported definition. It should be in the form of::

            {
                "KEY1": "value1",
                "KEY2": "value2",
            }

    :param command: Define a command to run within the exported wrapper. Default
        is None.

    :param packages: Indicate a list of :class:`wiz.package.Package` instances
        which helped creating the context.

    :return: Path to the exported script.

    :raise: :exc:`ValueError` if the *script_type* is incorrect.

    :raise: :exc:`ValueError` if *environ* mapping is empty.

    :raise: :exc:`OSError` if the wrapper can not be exported in *path*.

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

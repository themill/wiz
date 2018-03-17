# :coding: utf-8

from __future__ import print_function
import argparse
import os
import itertools
import shlex

import mlog
from packaging.requirements import Requirement
from packaging.version import Version, InvalidVersion

import wiz.registry
import wiz.symbol
import wiz.definition
import wiz.package
import wiz.spawn
import wiz.exception
import wiz.filesystem


def construct_parser():
    """Return argument parser."""
    parser = argparse.ArgumentParser(
        prog="wiz",
        description="Environment manager.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Allow setting of logging level from arguments.
    parser.add_argument(
        "-v", "--verbosity",
        help="Set the logging output verbosity.",
        choices=mlog.levels,
        default="info"
    )

    parser.add_argument(
        "--no-local",
        help="Skip local registry.",
        action="store_true"
    )

    parser.add_argument(
        "--no-cwd",
        help=(
            "Do not attempt to discover definitions from current "
            "working directory within project."
        ),
        action="store_true"
    )

    parser.add_argument(
        "-dsd", "--definition-search-depth",
        help="Maximum depth to recursively search for definitions.",
        type=int
    )

    subparsers = parser.add_subparsers(
        title="Commands",
        dest="commands"
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List available command or package definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    list_subparsers = list_parser.add_subparsers(
        title="Additional subcommands",
        dest="subcommands"
    )

    command_parser = list_subparsers.add_parser(
        "command",
        help="List all available commands.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    command_parser.add_argument(
        "--all",
        help="Return all definition versions.",
        action="store_true"
    )

    command_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    package_parser = list_subparsers.add_parser(
        "package",
        help="List all available packages.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    package_parser.add_argument(
        "--all",
        help="Return all definition versions.",
        action="store_true"
    )

    package_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    search_parser.add_argument(
        "--all",
        help="Return all definition versions.",
        action="store_true"
    )

    search_parser.add_argument(
        "-t", "--type",
        help="Set the type of definitions requested.",
        choices=[
            "all",
            wiz.symbol.PACKAGE_REQUEST_TYPE,
            wiz.symbol.COMMAND_REQUEST_TYPE
        ],
        default="all"
    )

    search_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    search_parser.add_argument(
        "requirements",
        nargs="+",
        help="Package requirements to search."
    )

    view_subparsers = subparsers.add_parser(
        "view",
        help="View content of a package definition.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    view_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    view_subparsers.add_argument(
        "requirement",
        help="Environment or Application identifier required."
    )

    run_subparsers = subparsers.add_parser(
        "run",
        help="Run command from package.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    run_subparsers.add_argument(
        "--view",
        help="Only view the resolved context.",
        action="store_true"
    )

    run_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    run_subparsers.add_argument(
        "requirement", help="Command requirement to run."
    )

    use_subparsers = subparsers.add_parser(
        "use",
        help=(
            "Spawn shell with resolved context from requirements, or run "
            "a command within the resolved context if indicated after "
            "the '--' symbol."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    use_subparsers.add_argument(
        "--view",
        help="Only view the resolved context.",
        action="store_true"
    )

    use_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    use_subparsers.add_argument(
        "requirements",
        nargs="+",
        help="Package requirements required."
    )

    freeze_subparsers = subparsers.add_parser(
        "freeze",
        help="Output resolved context.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    freeze_subparsers.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Indicate the output directory.",
        required=True
    )

    freeze_subparsers.add_argument(
        "-f", "--format",
        help="Indicate the output format.",
        choices=["wiz", "tcsh", "bash"],
        default="wiz"
    )

    freeze_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    freeze_subparsers.add_argument(
        "requirements",
        nargs="+",
        help="Package requirements required."
    )

    return parser


def main(arguments=None):
    """Wiz command line interface."""
    if arguments is None:
        arguments = []

    mlog.configure()
    logger = mlog.Logger(__name__ + ".main")

    # Extract the command section of the arguments list if necessary
    command_arguments = None

    if wiz.symbol.COMMAND_SEPARATOR in arguments:
        index = arguments.index(wiz.symbol.COMMAND_SEPARATOR)
        command_arguments = arguments[index+1:]
        arguments = arguments[:index]

    if command_arguments is not None and len(command_arguments) == 0:
        logger.error(
            "The command indicated after the symbol '{}' is "
            "incorrect.".format(wiz.symbol.COMMAND_SEPARATOR),
        )
        return

    # Process arguments.
    parser = construct_parser()
    namespace = parser.parse_args(arguments)

    # Set verbosity level.
    mlog.root.handlers["stderr"].filterer.filterers[0].min = namespace.verbosity

    # Identify system mapping.
    system_mapping = wiz.system.query()
    logger.debug("System: {}".format(system_mapping))

    # Fetch all registries.
    registries = wiz.registry.fetch(
        namespace.definition_search_paths,
        include_local=not namespace.no_local,
        include_working_directory=not namespace.no_cwd
    )
    logger.debug("Registries: " + ", ".join(registries))

    # Process requested operation.
    if namespace.commands == "list":
        _fetch_and_display_definitions(namespace, registries, system_mapping)

    elif namespace.commands == "search":
        _search_and_display_definitions(
            namespace, registries, system_mapping
        )

    elif namespace.commands == "view":
        _display_definition(
            namespace, registries, system_mapping
        )

    elif namespace.commands == "use":
        _resolve_and_use_context(
            namespace, registries, command_arguments, system_mapping
        )

    elif namespace.commands == "run":
        _run_command(
            namespace, registries, command_arguments, system_mapping
        )

    elif namespace.commands == "freeze":
        _freeze_and_export_resolved_context(
            namespace, registries, system_mapping
        )


def _fetch_and_display_definitions(namespace, registries, system_mapping):
    """Fetch and display definitions from arguments in *namespace*.

    Command example::

        wiz list application
        wiz list environment
        wiz list environment --all
        wiz list environment --with-aliases

    *namespace* is an instance of :class:`argparse.Namespace`.

    *registries* should be a list of available registry paths.

    *system_mapping* should be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    """
    mapping = wiz.fetch_definitions(
        registries,
        system_mapping=system_mapping,
        max_depth=namespace.definition_search_depth
    )
    display_registries(registries)

    if namespace.subcommands == "command":
        definition_mapping = {
            k: mapping[wiz.symbol.PACKAGE_REQUEST_TYPE][v]
            for (k, v) in mapping[wiz.symbol.COMMAND_REQUEST_TYPE].items()
        }

        display_definition_mapping(
            definition_mapping, registries,
            all_versions=namespace.all,
            command=True
        )

    elif namespace.subcommands == "package":
        display_definition_mapping(
            mapping[wiz.symbol.PACKAGE_REQUEST_TYPE], registries,
            all_versions=namespace.all,
        )


def _search_and_display_definitions(namespace, registries, system_mapping):
    """Search and display definitions from arguments in *namespace*.

    Command example::

        wiz search request
        wiz search request --all
        wiz search request>=2
        wiz search request other

    *namespace* is an instance of :class:`argparse.Namespace`.

    *registries* should be a list of available registry paths.

    *system_mapping* should be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    """
    logger = mlog.Logger(__name__ + "._search_and_display_definitions")

    mapping = wiz.definition.fetch(
        registries,
        requests=namespace.requirements,
        system_mapping=system_mapping,
        max_depth=namespace.definition_search_depth
    )

    display_registries(registries)
    results_found = False

    if (
        namespace.type in ["command", "all"] and
        len(mapping[wiz.symbol.COMMAND_REQUEST_TYPE]) > 0
    ):
        results_found = True
        definition_mapping = {
            k: mapping[wiz.symbol.PACKAGE_REQUEST_TYPE][v]
            for (k, v) in mapping[wiz.symbol.COMMAND_REQUEST_TYPE].items()
        }

        display_definition_mapping(
            definition_mapping, registries,
            all_versions=namespace.all,
            command=True
        )

    if (
        namespace.type in ["package", "all"] and
        len(mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]) > 0
    ):
        results_found = True
        display_definition_mapping(
            mapping[wiz.symbol.PACKAGE_REQUEST_TYPE], registries,
            all_versions=namespace.all,
        )

    if not results_found:
        logger.warning("No results found.\n")


def _display_definition(namespace, registries, system_mapping):
    """Display definition from arguments in *namespace*.

    Command example::

        wiz view app
        wiz view package

    *namespace* is an instance of :class:`argparse.Namespace`.

    *registries* should be a list of available registry paths.

    *system_mapping* should be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    """
    logger = mlog.Logger(__name__ + "._display_definition")

    mapping = wiz.fetch_definitions(
        registries,
        system_mapping=system_mapping,
        max_depth=namespace.definition_search_depth
    )

    def _display(_requirement):
        """Display definition from *requirement*."""
        _definition = wiz.definition.get(
            _requirement, mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
        )
        display_definition(_definition)
        return True

    requirement = Requirement(namespace.requirement)

    results_found = False

    # Check command mapping.
    if requirement.name in mapping[wiz.symbol.COMMAND_REQUEST_TYPE]:
        definition_requirement = Requirement(
            mapping[wiz.symbol.COMMAND_REQUEST_TYPE][requirement.name]
        )
        definition_requirement.specifier = requirement.specifier

        try:
            results_found = _display(definition_requirement)

        except wiz.exception.RequestNotFound:
            logger.debug(
                "No command found for request: '{}'\n".format(
                    requirement
                )
            )

    # Check package mapping.
    if requirement.name in mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]:
        try:
            results_found = _display(requirement)

        except wiz.exception.RequestNotFound:
            logger.debug(
                "No package found for request: '{}'\n".format(
                    requirement
                )
            )

    # Otherwise, print a warning...
    if not results_found:
        logger.warning(
            "No definition could be found for "
            "request: '{}'\n".format(namespace.requirement)
        )


def _resolve_and_use_context(
    namespace, registries, command_arguments, system_mapping
):
    """Resolve and use environment from arguments in *namespace*.

    Command example::

        wiz use package1>=1 package2==2.3.0 package3
        wiz use package1>=1 package2==2.3.0 package3 -- app --option value
        wiz use --view command

    *namespace* is an instance of :class:`argparse.Namespace`.

    *registries* should be a list of available registry paths.

    *command_arguments* could be the command list to execute within
    the resolved context.

    *system_mapping* should be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    """
    logger = mlog.Logger(__name__ + "._resolve_and_use_context")

    mapping = wiz.fetch_definitions(
        registries,
        system_mapping=system_mapping,
        max_depth=namespace.definition_search_depth
    )

    try:
        context = wiz.resolve_context(namespace.requirements, mapping)

        # Only view the resolved environment without spawning a shell nor
        # running any commands.
        if namespace.view:
            display_registries(registries)
            display_packages(context["packages"], registries)
            display_command_mapping(context.get("command", {}))
            display_environ_mapping(context.get("environ", {}))

        # If no commands are indicated, spawn a shell.
        elif command_arguments is None:
            wiz.spawn.shell(context["environ"])

        # Otherwise, resolve the command and run it within the resolved context.
        else:
            commands = command_arguments
            command_mapping = context.get("command", {})

            if commands[0] in command_mapping.keys():
                commands = (
                    shlex.split(command_mapping[commands[0]]) + commands[1:]
                )

            wiz.spawn.execute(commands, context["environ"])

    except wiz.exception.WizError as error:
        logger.error(str(error), traceback=True)


def _run_command(namespace, registries, command_arguments, system_mapping):
    """Run application from arguments in *namespace*.

    Command example::

        wiz run command
        wiz run command -- --option value /path/to/output

    *namespace* is an instance of :class:`argparse.Namespace`.

    *registries* should be a list of available registry paths.

    *command_arguments* could be the command list to execute within
    the resolved context.

    *system_mapping* should be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    """
    logger = mlog.Logger(__name__ + "._run_command")

    mapping = wiz.fetch_definitions(
        registries,
        system_mapping=system_mapping,
        max_depth=namespace.definition_search_depth
    )

    requirement = Requirement(namespace.requirement)

    commands = [requirement.name]
    if command_arguments is not None:
        commands += command_arguments

    definition_requirement = Requirement(
        mapping[wiz.symbol.COMMAND_REQUEST_TYPE][requirement.name]
    )
    definition_requirement.specifier = requirement.specifier

    try:
        context = wiz.resolve_context([str(definition_requirement)], mapping)

        # Only view the resolved environment without spawning a shell nor
        # running any commands.
        if namespace.view:
            display_registries(registries)
            display_packages(context["packages"], registries)
            display_command_mapping(context.get("command", {}))
            display_environ_mapping(context.get("environ", {}))

        else:
            command_mapping = context.get("command", {})

            if commands[0] in command_mapping.keys():
                commands = (
                    shlex.split(command_mapping[commands[0]]) + commands[1:]
                )

            wiz.spawn.execute(commands, context["environ"])

    except wiz.exception.WizError as error:
        logger.error(str(error), traceback=True)


def _freeze_and_export_resolved_context(namespace, registries, system_mapping):
    """Freeze resolved context from arguments in *namespace*.

    Command example::

        wiz freeze package1>=1 package2==2.3.0 package3
        wiz freeze --format bash package1>=1 package2==2.3.0 package3
        wiz freeze --format tcsh package1>=1 package2==2.3.0 package3

    *namespace* is an instance of :class:`argparse.Namespace`.

    *registries* should be a list of available registry paths.

    *system_mapping* should be a mapping of the current system, usually
    retrieved via :func:`wiz.system.query`.

    """
    logger = mlog.Logger(__name__ + "._freeze_and_export_resolved_context")

    mapping = wiz.fetch_definitions(
        registries,
        system_mapping=system_mapping,
        max_depth=namespace.definition_search_depth
    )

    try:
        context = wiz.resolve_context(namespace.requirements, mapping)

        if namespace.format == "wiz":
            definition_data = {
                "identifier": _query_identifier(logger),
                "description": _query_description(logger),
                "version": _query_version(logger),
                "command": context.get("command", {}),
                "environ": context.get("environ", {})
            }

            definition = wiz.definition.Definition(**definition_data)

            path = os.path.join(
                os.path.abspath(namespace.output),
                "{identifier}-{version}.json".format(
                    identifier=definition.identifier,
                    version=definition.version,
                )
            )

            wiz.filesystem.export(path, definition.encode())

        elif namespace.format in ["tcsh", "bash"]:
            path = os.path.join(
                os.path.abspath(namespace.output),
                _query_identifier(logger)
            )

            command = _query_command(context.get("command", {}).values())

            # Indicate information about the generation process.
            is_bash = namespace.format == "bash"
            content = (
                "#!/bin/bash\n" if is_bash else "#!/bin/tcsh -f\n"
                "#\n"
                "# Generated by wiz with the following environments:\n"
            )
            for package in context.get("packages"):
                content += "# - {}\n".format(package.identifier)
            content += "#\n"

            for key, value in context.get("environ", {}).items():
                # Do not override the PATH environment variable to prevent
                # error when executing the script.
                if key == "PATH":
                    value += ":${PATH}"

                if is_bash:
                    content += "export {0}=\"{1}\"\n".format(key, value)
                else:
                    content += "setenv {0} \"{1}\"\n".format(key, value)

            if command:
                content += command + (" $@" if is_bash else " $argv:q")

            wiz.filesystem.export(path, content)

    except wiz.exception.WizError as error:
        logger.error(str(error), traceback=True)

    except KeyboardInterrupt:
        logger.warning("Aborted.")


def display_registries(paths):
    """Display all registries from *paths* with an identifier.

    Example::

        >>> display_registries(paths)

        [0] /path/to/registry-1
        [1] /path/to/registry-2

    """
    title = "Registries"
    mappings = [
        {"size": len(title), "items": [], "title": title}
    ]

    for index, path in enumerate(paths):
        item = "[{}] {}".format(index, path)
        mappings[0]["items"].append(item)
        mappings[0]["size"] = max(len(item), mappings[0]["size"])

    _display_table(mappings)


def display_definition(definition):
    """Display *definition* instance.

    *definition* should be a :class:`wiz.definition.Definition` instance.

    Example::

        >>> display_definition(definition)

        identifier: app-env
        registry: /path/to/registry
        description: My Application Environment
        version: 0.1.0
        system:
            - os: el >= 7, < 8
            - arch: x86_64
        command:
            - app: App0.1.0
            - appX: app0.1.0 --option value
        environ:
            - KEY1: VALUE1
            - KEY2: VALUE2
            - KEY3: VALUE3
        requirements:
            - env1>=0.1
            - env2==1.0.2

    """
    logger = mlog.Logger(__name__ + ".display_definition")
    logger.info(
        "View environment: {} ({})".format(
            definition.identifier, definition.version
        )
    )

    print("identifier: {}".format(definition.identifier))
    print("registry: {}".format(definition.get("registry")))
    print("description: {}".format(definition.description))
    print("version: {}".format(definition.version))
    if len(definition.system) > 0:
        print("system:")
        for key, value in sorted(definition.system.items()):
            print("    - {}: {}".format(key, value))
    if len(definition.command) > 0:
        print("command:")
        for key, value in sorted(definition.command.items()):
            print("    - {}: {}".format(key, value))
    if len(definition.environ) > 0:
        print("environ:")
        for key, value in sorted(definition.environ.items()):
            print("    - {}: {}".format(key, value))
    if len(definition.requirements) > 0:
        print("requirements:")
        for requirement in definition.requirements:
            print("    - {}".format(requirement))
    if len(definition.variants) > 0:
        print("variants:")
        for variant in definition.variants:
            print("    - {}".format(variant.identifier))
            if len(variant.environ) > 0:
                print("        environ:")
                for key, value in sorted(variant.environ.items()):
                    print("            - {}: {}".format(key, value))
            if len(variant.requirements) > 0:
                print("        requirements:")
                for requirement in variant.requirements:
                    print("            - {}".format(requirement))

    print()


def display_definition_mapping(
    mapping, registries, all_versions=False, command=False
):
    """Display definition contained in *mapping*.

    *mapping* is a mapping regrouping all available definition versions
    associated with their unique identifier.

    *registries* should be a list of available registry paths.

    *all_versions* indicate whether all versions from the definition must be
    returned. If not, only the latest version of each definition identifier is
    displayed.

    *command* indicate whether the mapping identifiers represent commands.

    """
    identifiers = []
    definitions = []

    for identifier in sorted(mapping.keys()):
        versions = sorted(
            map(lambda d: d.version, mapping[identifier].values()),
            reverse=True
        )

        for index in range(len(versions)):
            if index > 0 and not all_versions:
                break

            identifiers.append(identifier)
            definitions.append(mapping[identifier][str(versions[index])])

    header = "Command" if command else "Package"
    titles = [header, "Version", "Registry", "Description"]
    rows = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    def _format_unit(_identifier, _definition, _variant=None):
        """Format row unit."""
        if _variant is not None:
            _identifier += " [{}]".format(_variant)

        rows[0]["items"].append(_identifier)
        rows[0]["size"] = max(len(_identifier), rows[0]["size"])

        _version = str(_definition.version)
        rows[1]["items"].append(_version)
        rows[1]["size"] = max(len(_version), rows[1]["size"])

        registry_index = str(registries.index(_definition.get("registry")))
        rows[2]["items"].append(registry_index)
        rows[2]["size"] = max(len(registry_index), rows[2]["size"])

        _description = _definition.description
        rows[3]["items"].append(_description)
        rows[3]["size"] = max(len(_description), rows[3]["size"])

    for identifier, definition in itertools.izip_longest(
        identifiers, definitions
    ):
        if len(definition.variants) > 0:
            for variant in definition.variants:
                _variant = variant.identifier
                _format_unit(identifier, definition, _variant)

        else:
            _format_unit(identifier, definition)

    _display_table(rows)


def display_packages(packages, registries):
    """Display *packages*.

    *packages* should be a list of :class:`wiz.package.Package` instances.

    *registries* should be a list of available registry paths.

    """
    titles = ["Package", "Version", "Registry", "Description"]
    rows = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    for package in packages:
        _identifier = package.definition.identifier
        if package.variant_name is not None:
            _identifier += " [{}]".format(package.variant_name)

        rows[0]["items"].append(_identifier)
        rows[0]["size"] = max(len(_identifier), rows[0]["size"])

        _version = str(package.version)
        rows[1]["items"].append(_version)
        rows[1]["size"] = max(len(_version), rows[1]["size"])

        registry_index = str(
            registries.index(package.definition.get("registry"))
        )
        rows[2]["items"].append(registry_index)
        rows[2]["size"] = max(len(registry_index), rows[2]["size"])

        _description = package.description
        rows[3]["items"].append(_description)
        rows[3]["size"] = max(len(_description), rows[3]["size"])

    _display_table(rows)


def display_command_mapping(mapping):
    """Display commands contained in *mapping*.

    *mapping* should be in the form of::

        {
            "app": "App0.1.0",
            "appX": "App0.1.0 --option value"
        }

    """
    if len(mapping) == 0:
        print("No command to display.")
        return

    titles = ["Command", "Value"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    for command, value in sorted(mapping.items()):
        mappings[0]["items"].append(command)
        mappings[0]["size"] = max(len(command), mappings[0]["size"])

        mappings[1]["items"].append(value)
        mappings[1]["size"] = max(len(value), mappings[1]["size"])

    _display_table(mappings)


def display_environ_mapping(mapping):
    """Display environment variables contained in *mapping*.

    *mapping* should be in the form of::

        {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2"
        }

    """
    if len(mapping) == 0:
        print("No environment variables to display.")
        return

    titles = ["Environment Variable", "Environment Value"]
    rows = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    def _compute_value(_variable, value):
        """Compute value to display."""
        if _variable == "DISPLAY":
            return [value]
        return str(value).split(os.pathsep)

    for variable in sorted(mapping.keys()):
        for key, _value in itertools.izip_longest(
            [variable], _compute_value(variable, mapping[variable])
        ):
            _key = key or ""
            rows[0]["items"].append(_key)
            rows[0]["size"] = max(len(_key), rows[0]["size"])

            rows[1]["items"].append(_value)
            rows[1]["size"] = max(len(_value), rows[1]["size"])

    _display_table(rows)


def _query_identifier(logger):
    """Query an identifier for a resolved environment."""
    while True:
        print("Indicate an identifier:", end=" ")
        identifier = wiz.filesystem.sanitise_value(raw_input().strip())
        if len(identifier) > 3:
            return identifier

        logger.warning(
            "'{}' is an incorrect identifier (It must be at least 3 "
            "characters long.)".format(identifier)
        )


def _query_description(logger):
    """Query an description for a resolved environment."""
    while True:
        print("Indicate a description:", end=" ")
        description = raw_input().strip()

        if len(description) > 5:
            return description

        logger.warning(
            "'{}' is an incorrect description (It must be at least 5 "
            "characters long.)".format(description)
        )


def _query_version(logger, default="0.1.0"):
    """Query a version for a resolved environment."""
    while True:
        print("Indicate a version [{}]:".format(default), end=" ")
        version = raw_input() or default

        try:
            Version(version)
        except InvalidVersion:
            logger.warning("'{}' is an incorrect version".format(version))
            continue

        return version


def _query_command(aliases=None):
    """Query the commands to run within the exported wrapper."""
    if aliases > 0:
        print("Available aliases:")
        for _command in aliases:
            print("- {}".format(_command))
    print("Indicate a command (No command by default):", end=" ")
    command = raw_input()
    if len(command):
        return command


def _display_table(rows):
    """Display table of *rows*."""
    spaces = []
    for column in rows:
        space = column["size"] - len(column["title"])
        spaces.append(space)

    # Print titles.
    print(
        "\n" + "   ".join([
            rows[i]["title"] + " " * spaces[i]
            for i in range(len(rows))
        ])
    )

    # Print underlines.
    print(
        "   ".join([
            "-" * (len(rows[i]["title"]) + spaces[i])
            for i in range(len(rows))
        ])
    )

    # Print elements.
    for elements in itertools.izip(*[column["items"] for column in rows]):
        print(
            "   ".join([
                elements[i] + " " * (rows[i]["size"] - len(elements[i]))
                for i in range(len(elements))
            ])
        )

    # Print final blank line.
    print()

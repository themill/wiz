# :coding: utf-8

from __future__ import print_function
import argparse
import os
import itertools
import shlex
import collections

import mlog
from packaging.version import Version, InvalidVersion

import wiz.registry
import wiz.symbol
import wiz.definition
import wiz.package
import wiz.spawn
import wiz.exception
import wiz.filesystem
import wiz.history


def construct_parser():
    """Return argument parser."""
    parser = argparse.ArgumentParser(
        prog="wiz",
        description="Package manager.",
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

    parser.add_argument(
        "--platform",
        help="Override the detected platform.",
        metavar="PLATFORM",
    )

    parser.add_argument(
        "--arch",
        help="Override the detected architecture.",
        metavar="ARCH",
    )

    parser.add_argument(
        "--os-name",
        help="Override the detected operating system name.",
        metavar="OS_NAME",
    )

    parser.add_argument(
        "--os-version",
        help="Override the detected operating system version.",
        metavar="OS_VERSION",
    )

    parser.add_argument(
        "--record",
        help="Record resolution context process for debugging.",
        metavar="PATH"
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
        "requests",
        nargs="+",
        help="Package requested."
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
        "--json",
        help="Display definition in JSON.",
        action="store_true"
    )

    view_subparsers.add_argument(
        "request",
        help="Package identifier required."
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
        "request", help="Command requested to run."
    )

    use_subparsers = subparsers.add_parser(
        "use",
        help=(
            "Spawn shell with resolved context from requested packages, or run "
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
        "requests",
        nargs="+",
        help="Package identifiers required."
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
        "requests",
        nargs="+",
        help="Package identifiers required."
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

    if namespace.record is not None:
        command = "wiz {}".format(" ".join(arguments))
        wiz.history.start_recording(command=command)

    # Set verbosity level.
    mlog.root.handlers["stderr"].filterer.filterers[0].min = namespace.verbosity

    # Identify system mapping.
    system_mapping = wiz.system.query(
        platform=namespace.platform,
        architecture=namespace.arch,
        os_name=namespace.os_name,
        os_version=namespace.os_version,
    )
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

        wiz list command
        wiz list package
        wiz list package --all
        wiz list command --all

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
        requests=namespace.requests,
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
        wiz view package --json

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

    results_found = False

    request_types = [
        wiz.symbol.COMMAND_REQUEST_TYPE,
        wiz.symbol.PACKAGE_REQUEST_TYPE
    ]

    # Track origins to prevent the display of a definition twice.
    _origins = set()

    for request_type in request_types:
        try:
            definition = wiz.query_definition(
                namespace.request, mapping, request_type=request_type
            )
            results_found = True

        except wiz.exception.RequestNotFound as exception:
            logger.debug(
                "Impossible to query definition for {} request "
                "type: {}\n".format(request_type, exception)
            )

        else:
            if definition.get("origin") not in _origins:
                if namespace.json:
                    print(definition.encode())
                else:
                    display_definition(definition)

            _origins.add(definition.get("origin"))

    # Otherwise, print a warning...
    if not results_found:
        logger.warning(
            "No definition could be found for "
            "request: '{}'\n".format(namespace.request)
        )


def _resolve_and_use_context(
    namespace, registries, command_arguments, system_mapping
):
    """Resolve and use context from arguments in *namespace*.

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
        context = wiz.resolve_package_context(namespace.requests, mapping)

        # Only view the resolved context without spawning a shell nor
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
            resolved_command = wiz.resolve_command(
                command_arguments, context.get("command", {})
            )

            wiz.spawn.execute(
                shlex.split(resolved_command), context["environ"]
            )

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

    try:
        context = wiz.resolve_command_context(
            namespace.request, mapping, arguments=command_arguments
        )

        # Only view the resolved context without spawning a shell nor
        # running any commands.
        if namespace.view:
            display_registries(registries)
            display_packages(context["packages"], registries)
            display_command_mapping(context.get("command", {}))
            display_environ_mapping(context.get("environ", {}))

        else:
            wiz.spawn.execute(
                shlex.split(context["resolved_command"]),
                context["environ"]
            )

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
        context = wiz.resolve_package_context(namespace.requests, mapping)
        identifier = _query_identifier(logger)

        if namespace.format == "wiz":
            description = _query_description(logger)
            version = _query_version(logger)

            wiz.export_definition(
                namespace.output, identifier, description,
                version=version,
                command_mapping=context.get("command"),
                environ_mapping=context.get("environ")
            )

        elif namespace.format == "bash":
            command = _query_command(context.get("command", {}).values())
            wiz.export_bash_wrapper(
                namespace.output, identifier,
                command=command,
                environ_mapping=context.get("environ"),
                packages=context.get("packages")
            )

        elif namespace.format == "tcsh":
            command = _query_command(context.get("command", {}).values())
            wiz.export_csh_wrapper(
                namespace.output, identifier,
                command=command,
                environ_mapping=context.get("environ"),
                packages=context.get("packages")
            )

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

    """
    logger = mlog.Logger(__name__ + ".display_definition")
    logger.info(
        "View definition: {} ({})".format(
            definition.identifier, definition.version
        )
    )

    def _display(item, level=0):
        """Display *mapping*"""
        indent = " "*level
        if isinstance(item, collections.OrderedDict) or isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, basestring) or isinstance(value, int):
                    print("{}{}: {}".format(indent, key, value))
                else:
                    print("{}{}:".format(indent, key))
                    _display(value, level=level + 4)

        elif isinstance(item, list) or isinstance(item, tuple):
            for _item in item:
                _display(_item, level=level + 4)

        else:
            print("{}{}".format(indent, item))

    _display(definition.to_ordered_mapping())
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
        _identifier = package.definition_identifier
        if package.variant_name is not None:
            _identifier += " [{}]".format(package.variant_name)

        rows[0]["items"].append(_identifier)
        rows[0]["size"] = max(len(_identifier), rows[0]["size"])

        _version = str(package.version)
        rows[1]["items"].append(_version)
        rows[1]["size"] = max(len(_version), rows[1]["size"])

        registry_index = str(
            registries.index(package.get("registry"))
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
        if _variable == "WIZ_PACKAGES":
            return [value[:50] + "..."]
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
    """Query an identifier for a resolved context."""
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
    """Query an description for a resolved context."""
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
    """Query a version for a resolved context."""
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

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
import wiz.environment
import wiz.application
import wiz.spawn
import wiz.exception
import wiz.filesystem


def construct_parser():
    """Return argument parser."""
    parser = argparse.ArgumentParser(
        prog="wiz",
        description="Fetch and create run-time environments.",
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
        help="List available application or environment definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    list_subparsers = list_parser.add_subparsers(
        title="Additional subcommands",
        dest="subcommands"
    )

    application_parser = list_subparsers.add_parser(
        "application",
        help="List all available applications.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    application_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    environment_parser = list_subparsers.add_parser(
        "environment",
        help="List all available environments.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    environment_parser.add_argument(
        "--all",
        help="Return all environment versions.",
        action="store_true"
    )

    environment_parser.add_argument(
        "--with-commands",
        help="Return only environment defining commands.",
        action="store_true"
    )

    environment_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search environment or application definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    search_parser.add_argument(
        "--all",
        help="Return all environment versions.",
        action="store_true"
    )

    search_parser.add_argument(
        "--with-commands",
        help="Return only environment defining commands.",
        action="store_true"
    )

    search_parser.add_argument(
        "-t", "--type",
        help="Set the type of definitions requested.",
        choices=[
            "all",
            wiz.symbol.APPLICATION_TYPE,
            wiz.symbol.ENVIRONMENT_TYPE
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
        help="Environment or application requirements to search."
    )

    view_subparsers = subparsers.add_parser(
        "view",
        help="View content of an environment or application definition.",
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
        help="Run command from application.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    run_subparsers.add_argument(
        "--view",
        help="Only view the resolved environment.",
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
        "application", help="Application identifier to run."
    )

    use_subparsers = subparsers.add_parser(
        "use",
        help=(
            "Spawn shell with resolved environment from requirements, or run "
            "a command within the resolved environment if indicated after "
            "the '--' symbol."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    use_subparsers.add_argument(
        "--view",
        help="Only view the resolved environment.",
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
        help="Environment requirements required."
    )

    freeze_subparsers = subparsers.add_parser(
        "freeze",
        help="Output resolved environment.",
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
        help="Environment requirements required."
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

    # Fetch all registries.
    registries = wiz.registry.fetch(
        namespace.definition_search_paths,
        include_local=not namespace.no_local,
        include_working_directory=not namespace.no_cwd
    )
    logger.debug("Registries: " + ", ".join(registries))

    # Process requested operation.
    if namespace.commands == "list":
        if namespace.subcommands == "application":
            mapping = wiz.definition.fetch(
                registries, max_depth=namespace.definition_search_depth
            )
            display_registries(registries)
            display_applications_mapping(
                mapping[wiz.symbol.APPLICATION_TYPE],
                registries
            )

        elif namespace.subcommands == "environment":
            mapping = wiz.definition.fetch(
                registries, max_depth=namespace.definition_search_depth
            )
            display_registries(registries)
            display_environment_mapping(
                mapping[wiz.symbol.ENVIRONMENT_TYPE],
                registries,
                all_versions=namespace.all,
                commands_only=namespace.with_commands
            )

    elif namespace.commands == "search":
        requirements = map(Requirement, namespace.requirements)
        mapping = wiz.definition.search(
            requirements, registries,
            max_depth=namespace.definition_search_depth
        )

        display_registries(registries)
        results_found = False

        if (
            namespace.type in ["application", "all"] and
            len(mapping[wiz.symbol.APPLICATION_TYPE]) > 0
        ):
            results_found = True
            display_applications_mapping(
                mapping[wiz.symbol.APPLICATION_TYPE],
                registries
            )

        if (
            namespace.type in ["environment", "all"] and
            len(mapping[wiz.symbol.ENVIRONMENT_TYPE]) > 0
        ):
            results_found = True
            display_environment_mapping(
                mapping[wiz.symbol.ENVIRONMENT_TYPE],
                registries,
                all_versions=namespace.all,
                commands_only=namespace.with_commands
            )

        if not results_found:
            logger.warning("No results found.\n")

    elif namespace.commands == "view":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        results_found = False

        try:
            application = wiz.application.get(
                namespace.requirement,
                mapping[wiz.symbol.APPLICATION_TYPE]
            )
            results_found = True

        except wiz.exception.RequestNotFound:
            logger.debug(
                "No application found for requirement: '{}'\n".format(
                    namespace.requirement
                )
            )

        else:
            display_application(application, logger)

        try:
            requirement = Requirement(namespace.requirement)
            environment = wiz.environment.get(
                requirement, mapping[wiz.symbol.ENVIRONMENT_TYPE],
                divide_variants=False
            )[0]
            results_found = True

        except wiz.exception.RequestNotFound:
            logger.debug(
                "No environment found for requirement: '{}'\n".format(
                    namespace.requirement
                )
            )

        else:
            display_environment(environment, logger)

        if not results_found:
            logger.warning(
                "No application nor environment could be found for "
                "requirement: '{}'\n".format(namespace.requirement)
            )

    elif namespace.commands == "use":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        requirements = map(Requirement, namespace.requirements)

        try:
            environments = wiz.environment.resolve(
                requirements, mapping[wiz.symbol.ENVIRONMENT_TYPE]
            )

            data_mapping = wiz.environment.initiate_data()
            environment = wiz.environment.combine(
                environments, data_mapping=data_mapping
            )

            # Only view the resolved environment without spawning a shell nor
            # running any commands.
            if namespace.view:
                display_registries(registries)

                display_environments(
                    environments, registries,
                    header="Resolved Environments"
                )

                display_environment_commands(
                    environment.get("command", {}),
                    header="Resolved Commands"
                )

                display_environment_data(environment.get("data", {}))

            # If no commands are indicated, spawn a shell.
            elif command_arguments is None:
                wiz.spawn.shell(environment["data"])

            # Otherwise, resolve the command and run it within the resolved
            # environment.
            else:
                command_mapping = environment.get("command", {})
                if command_arguments[0] in command_mapping.keys():
                    commands = shlex.split(
                        command_mapping[command_arguments[0]]
                    )
                    command_arguments = commands + command_arguments[1:]

                wiz.spawn.execute(command_arguments, environment["data"])

        except wiz.exception.WizError as error:
            logger.error(str(error), traceback=True)

    elif namespace.commands == "run":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        try:
            application = wiz.application.get(
                namespace.application, mapping[wiz.symbol.APPLICATION_TYPE]
            )

            environments = wiz.application.resolve_environments(
                application, mapping[wiz.symbol.ENVIRONMENT_TYPE]
            )

            data_mapping = wiz.environment.initiate_data()
            environment = wiz.environment.combine(
                environments, data_mapping=data_mapping
            )

            commands = wiz.application.extract_commands(
                application, environment, arguments=command_arguments
            )

            # Only view the resolved environment without running any commands.
            if namespace.view:
                logger.info("Start command: {}".format(" ".join(commands)))

                display_registries(registries)

                display_environments(
                    environments, registries,
                    header="Resolved Environments"
                )

                display_environment_data(environment.get("data", {}))

            else:
                wiz.spawn.execute(commands, environment["data"])

        except wiz.exception.WizError as error:
            logger.error(str(error), traceback=True)

    elif namespace.commands == "freeze":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        requirements = map(Requirement, namespace.requirements)

        try:
            environments = wiz.environment.resolve(
                requirements, mapping[wiz.symbol.ENVIRONMENT_TYPE]
            )

            if namespace.format == "wiz":
                environment_data = {
                    "identifier": _query_identifier(logger),
                    "description": _query_description(logger),
                    "version": _query_version(logger),
                    "requirement": map(
                        wiz.environment.generate_identifier, environments
                    ),
                    "type": wiz.symbol.ENVIRONMENT_TYPE
                }

                environment = wiz.definition.create(environment_data)

                path = os.path.join(
                    os.path.abspath(namespace.output),
                    "{identifier}-{version}.json".format(
                        identifier=environment.identifier,
                        version=environment.version,
                    )
                )

                wiz.filesystem.export(path, environment.encode())

            elif namespace.format in ["tcsh", "bash"]:
                environment = wiz.environment.combine(environments)

                path = os.path.join(
                    os.path.abspath(namespace.output),
                    _query_identifier(logger)
                )

                command = _query_command(
                    environment.get("command", {}).values()
                )

                # Indicate information about the generation process.
                is_bash = namespace.format == "bash"
                content = (
                    "#!/bin/bash\n" if is_bash else "#!/bin/tcsh -f\n"
                    "#\n"
                    "# Generated by wiz with the following environments:\n"
                )
                for _environment in environments:
                    content += "# - {}\n".format(
                        wiz.environment.generate_identifier(_environment)
                    )
                content += "#\n"

                for key, value in environment.get("data", {}).items():
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


def _query_command(commands=None):
    """Query the commands to run within the exported wrapper."""
    if commands > 0:
        print("Available commands:")
        for _command in commands:
            print("- {}".format(_command))
    print("Indicate a command (No command by default):", end=" ")
    command = raw_input()
    if len(command):
        return command


def display_registries(paths):
    title = "Registries"
    mappings = [
        {"size": len(title), "items": [], "title": title}
    ]

    for index, path in enumerate(paths):
        item = "[{}] {}".format(index, path)
        mappings[0]["items"].append(item)
        mappings[0]["size"] = max(len(item), mappings[0]["size"])

    _display_mappings(mappings)


def display_application(application, logger):
    logger.info("View application: {}".format(application.identifier))

    print("identifier: {}".format(application.identifier))
    print("registry: {}".format(application.get("registry")))
    print("description: {}".format(application.description))
    print("command: {}".format(application.command))
    print("requirement:")
    for requirement in application.requirement:
        print("    - {}".format(requirement))
    print()


def display_environment(environment, logger):
    logger.info(
        "View environment: {} ({})".format(
            environment.identifier, environment.version
        )
    )

    print("identifier: {}".format(environment.identifier))
    print("registry: {}".format(environment.get("registry")))
    print("description: {}".format(environment.description))
    print("version: {}".format(environment.version))
    if len(environment.get("system", {})) > 0:
        print("system:")
        for key, value in sorted(environment.get("system").items()):
            print("    - {}: {}".format(key, value))
    if len(environment.get("command", {})) > 0:
        print("command:")
        for key, value in sorted(environment.get("command").items()):
            print("    - {}: {}".format(key, value))
    if len(environment.get("data", {})) > 0:
        print("data:")
        for key, value in sorted(environment.get("data").items()):
            print("    - {}: {}".format(key, value))
    if len(environment.get("requirement", [])) > 0:
        print("requirement:")
        for requirement in environment.get("requirement"):
            print("    - {}".format(requirement))
    if len(environment.get("variant", [])) > 0:
        print("variant:")
        for variant in environment.get("variant"):
            print("    - {}".format(variant.get("identifier")))
            if len(variant.get("data", {})) > 0:
                print("        data:")
                for key, value in sorted(variant.get("data").items()):
                    print("            - {}: {}".format(key, value))
            if len(variant.get("requirement", [])) > 0:
                print("        requirement:")
                for requirement in variant.get("requirement"):
                    print("            - {}".format(requirement))

    print()


def display_applications_mapping(application_mapping, registries):
    """Display the applications stored in *application_mapping*.

    *application_mapping* is a mapping regrouping all available application
    associated with their unique identifier.

    *registries* should be a list of available registry paths.

    """
    titles = ["Application", "Registry", "Description"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    for _, application in sorted(application_mapping.items()):
        _identifier = application.identifier
        mappings[0]["items"].append(_identifier)
        mappings[0]["size"] = max(len(_identifier), mappings[0]["size"])

        registry_index = str(registries.index(application.get("registry")))
        mappings[1]["items"].append(registry_index)
        mappings[1]["size"] = max(len(registry_index), mappings[1]["size"])

        description = application.description
        mappings[2]["items"].append(description)
        mappings[2]["size"] = max(len(description), mappings[2]["size"])

    _display_mappings(mappings)


def display_environment_mapping(
    environment_mapping, registries, all_versions=False, commands_only=False,
):
    """Display the environments stored in *environment_mapping*.

    *environment_mapping* is a mapping regrouping all available environment
    environment associated with their unique identifier.

    *registries* should be a list of available registry paths.

    *all_versions* indicate whether all versions from the environments must be
    returned. If not, only the latest version of each environment identifier is
    displayed.

    *commands_only* indicate whether only environments with 'commands' should be
    displayed.

    """
    environments_to_display = []

    for _, environments in sorted(environment_mapping.items()):
        _environments = sorted(
            environments, key=lambda _env: _env.version, reverse=True
        )

        if all_versions:
            for environment in _environments:
                environments_to_display.append(environment)
        else:
            environments_to_display.append(_environments[0])

    display_environments(
        environments_to_display, registries, commands_only=commands_only
    )


def display_environments(
    environments, registries, header=None, commands_only=False
):
    titles = [header or "Environment", "Version", "Registry", "Description"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    def _format_unit(_environment, _variant=None):
        """Format *_mapping* from *_environment* unit with optional *_variant*.
        """
        if commands_only and _environment.get("command") is None:
            return

        _identifier = _environment.identifier
        if _variant is not None:
            _identifier += " [{}]".format(_variant)

        mappings[0]["items"].append(_identifier)
        mappings[0]["size"] = max(len(_identifier), mappings[0]["size"])

        _version = str(_environment.version)
        mappings[1]["items"].append(_version)
        mappings[1]["size"] = max(len(_version), mappings[1]["size"])

        registry_index = str(registries.index(_environment.get("registry")))
        mappings[2]["items"].append(registry_index)
        mappings[2]["size"] = max(len(registry_index), mappings[2]["size"])

        _description = _environment.description
        mappings[3]["items"].append(_description)
        mappings[3]["size"] = max(len(_description), mappings[3]["size"])

    for environment in environments:
        if len(environment.get("variant", [])) > 0:
            for variant in environment.get("variant"):
                _variant = variant.get("identifier", "unknown")
                _format_unit(environment, _variant)

        else:
            _format_unit(environment, environment.get("variant_name"))

    _display_mappings(mappings)


def display_environment_commands(command_mapping, header=None):
    if len(command_mapping) == 0:
        print("No commands to display.")
        return

    titles = [header or "Commands", "Value"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    for command, value in sorted(command_mapping.items()):
        mappings[0]["items"].append(command)
        mappings[0]["size"] = max(len(command), mappings[0]["size"])

        mappings[1]["items"].append(value)
        mappings[1]["size"] = max(len(value), mappings[1]["size"])

    _display_mappings(mappings)


def display_environment_data(data_mapping):
    if len(data_mapping) == 0:
        print("No environment variables to display.")
        return

    titles = ["Environment Variable", "Environment Value"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    def _compute_value(_variable, value):
        """Compute value to display."""
        if _variable == "DISPLAY":
            return [value]
        return str(value).split(os.pathsep)

    for variable in sorted(data_mapping.keys()):
        for key, _value in itertools.izip_longest(
            [variable], _compute_value(variable, data_mapping[variable])
        ):
            _key = key or ""
            mappings[0]["items"].append(_key)
            mappings[0]["size"] = max(len(_key), mappings[0]["size"])

            mappings[1]["items"].append(_value)
            mappings[1]["size"] = max(len(_value), mappings[1]["size"])

    _display_mappings(mappings)


def _display_mappings(mappings):
    """Display *mapping*."""
    spaces = []
    for mapping in mappings:
        space = mapping["size"] - len(mapping["title"])
        spaces.append(space)

    # Print titles.
    print(
        "\n" + "   ".join([
            mappings[i]["title"] + " " * spaces[i]
            for i in range(len(mappings))
        ])
    )

    # Print underlines.
    print(
        "   ".join([
            "-" * (len(mappings[i]["title"]) + spaces[i])
            for i in range(len(mappings))
        ])
    )

    # Print elements.
    for elements in itertools.izip(*[mapping["items"] for mapping in mappings]):
        print(
            "   ".join([
                elements[i] + " " * (mappings[i]["size"] - len(elements[i]))
                for i in range(len(elements))
            ])
        )

    # Print final blank line.
    print()

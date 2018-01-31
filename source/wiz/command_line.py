# :coding: utf-8

from __future__ import print_function
import argparse
import os
import itertools

import mlog
from packaging.requirements import Requirement

import wiz.registry
import wiz.symbol
import wiz.definition
import wiz.environment
import wiz.application
import wiz.spawn
import wiz.exception


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

    application_parser = subparsers.add_parser(
        "applications",
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

    environment_parser = subparsers.add_parser(
        "environments",
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
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    search_parser.add_argument(
        "requirement",
        help="Environment or Application requirement to search."
    )

    view_subparsers = subparsers.add_parser(
        "view",
        help="View resolved environment from requirements.",
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
        "requirements",
        nargs="+",
        help="Environment requirements required."
    )

    load_subparsers = subparsers.add_parser(
        "load",
        help=(
            "Spawn shell with resolved environment from requirements, or run "
            "a command within the resolved environment if indicated after the "
            "'--' symbol."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    load_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    load_subparsers.add_argument(
        "requirements",
        nargs="+",
        help="Environment requirements required."
    )

    run_subparsers = subparsers.add_parser(
        "run",
        help="Run application command.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
    if namespace.commands == "applications":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        display_applications_mapping(
            mapping[wiz.symbol.APPLICATION_TYPE],
        )

    elif namespace.commands == "environments":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )
        display_environment_mapping(
            mapping[wiz.symbol.ENVIRONMENT_TYPE],
            all_versions=namespace.all,
            commands_only=namespace.with_commands
        )

    elif namespace.commands == "search":
        requirement = Requirement(namespace.requirement)
        mapping = wiz.definition.search(
            requirement, registries,
            max_depth=namespace.definition_search_depth
        )

        if (
            len(mapping[wiz.symbol.ENVIRONMENT_TYPE]) == 0 and
            len(mapping[wiz.symbol.APPLICATION_TYPE]) == 0
        ):
            print("No results found.")

        else:
            if len(mapping[wiz.symbol.APPLICATION_TYPE]):
                display_applications_mapping(
                    mapping[wiz.symbol.APPLICATION_TYPE]
                )

            if len(mapping[wiz.symbol.ENVIRONMENT_TYPE]):
                display_environment_mapping(
                    mapping[wiz.symbol.ENVIRONMENT_TYPE],
                    all_versions=namespace.all
                )

    elif namespace.commands in ["view", "load"]:
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        requirements = map(Requirement, namespace.requirements)

        try:
            if namespace.commands == "view":
                _resolve_and_display_environment(
                    requirements, mapping[wiz.symbol.ENVIRONMENT_TYPE]
                )

            elif namespace.commands == "load":
                environment = wiz.environment.resolve(
                    requirements, mapping[wiz.symbol.ENVIRONMENT_TYPE]
                )

                if command_arguments is None:
                    wiz.spawn.shell(environment["data"])

                else:
                    command_mapping = environment.get("command", {})
                    if command_arguments[0] in command_mapping.keys():
                        command_arguments[0] = (
                            command_mapping[command_arguments[0]]
                        )
                    wiz.spawn.execute(command_arguments, environment["data"])

        except wiz.exception.WizError as error:
            logger.error(
                "Impossible to resolve the environment: {}".format(error),
                traceback=True
            )

    elif namespace.commands in ["run"]:
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        try:
            application = wiz.application.get(
                namespace.application, mapping[wiz.symbol.APPLICATION_TYPE]
            )

            wiz.application.run(
                application, mapping[wiz.symbol.ENVIRONMENT_TYPE],
                arguments=command_arguments
            )

        except wiz.exception.WizError as error:
            logger.error(
                "Impossible to run the application: {}".format(error),
                traceback=True
            )


def _resolve_and_display_environment(requirements, environment_mapping):
    """Display content of resolved environment from *requirements*.

    *environment_mapping* is a mapping regrouping all available environment
    environment associated with their unique identifier.

    Raise :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
    resolved.

    """
    environments = wiz.environment.compute(requirements, environment_mapping)
    environment = wiz.environment.combine(environments)

    display_environments(environments, header="Resolved Environments")

    # Display Commands
    if len(environment.get("command", {})) > 0:
        display_environment_commands(environment.get("command"))

    # Display data
    display_environment_data(environment.get("data", {}))


def display_applications_mapping(application_mapping):
    """Display the applications stored in *application_mapping*.

    *application_mapping* is a mapping regrouping all available application
    associated with their unique identifier.

    """
    titles = ["Application", "Requirements", "Description"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    for _, application in sorted(application_mapping.items()):
        _identifier = application.identifier
        mappings[0]["items"].append(_identifier)
        mappings[0]["size"] = max(len(_identifier), mappings[0]["size"])

        requirement = ", ".join(map(str, application.requirement))
        mappings[1]["items"].append(requirement)
        mappings[1]["size"] = max(len(requirement), mappings[1]["size"])

        description = application.description
        mappings[2]["items"].append(description)
        mappings[2]["size"] = max(len(description), mappings[2]["size"])

    _display_mappings(mappings)


def display_environment_mapping(
    environment_mapping, all_versions=False, commands_only=False,
):
    """Display the environments stored in *environment_mapping*.

    *environment_mapping* is a mapping regrouping all available environment
    environment associated with their unique identifier.

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

    display_environments(environments_to_display, commands_only=commands_only)


def display_environments(environments, header=None, commands_only=False):
    titles = [header or "Environment", "Version", "Description"]
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

        _description = _environment.description
        mappings[2]["items"].append(_description)
        mappings[2]["size"] = max(len(_description), mappings[2]["size"])

    for environment in environments:
        if len(environment.get("variant", [])) > 0:
            for variant in environment.get("variant"):
                _variant = variant.get("identifier", "unknown")
                _format_unit(environment, _variant)

        else:
            _format_unit(environment, environment.get("variant_name"))

    _display_mappings(mappings)


def display_environment_commands(command_mapping):
    titles = ["Resolved Commands", "Value"]
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
    titles = ["Environment Variable", "Environment Value"]
    mappings = [
        {"size": len(title), "items": [], "title": title} for title in titles
    ]

    def _compute_value(_variable, value):
        """Compute value to display."""
        if _variable == "DISPLAY":
            return [value]
        return value.split(os.pathsep)

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

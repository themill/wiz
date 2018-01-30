# :coding: utf-8

from __future__ import print_function
import argparse
import os
import itertools

import mlog
from packaging.requirements import Requirement

import wiz.registry
import wiz.definition
import wiz.environment
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

    registries_parser = subparsers.add_parser(
        "registries",
        help="List all available registries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    registries_parser.add_argument(
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
        help="Return all versions of the environment definitions.",
        action="store_true"
    )

    environment_parser.add_argument(
        "--with-commands",
        help="Return only environment definitions with commands.",
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
        help="Search definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    search_parser.add_argument(
        "--all",
        help="Return all versions of the available environment definitions.",
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
        help="Definition requirement to search."
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
        help="Definition requirements required."
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
        help="Definition requirements required."
    )

    run_subparsers = subparsers.add_parser(
        "run",
        help="Run command within resolved environment from requirements.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    run_subparsers.add_argument(
        "--from",
        nargs="+",
        metavar="REQUIREMENT",
        dest="requirements",
        help="Indicate environment requirements required."
    )

    run_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for definitions.",
        default=wiz.registry.get_defaults()
    )

    run_subparsers.add_argument(
        "command",
        help="Command to run within resolved environment."
    )

    return parser


def main(arguments=None):
    """Wiz command line interface."""
    if arguments is None:
        arguments = []

    mlog.configure()
    logger = mlog.Logger(__name__ + ".main")

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
    if namespace.commands == "registries":
        print("\n".join(registries))

    elif namespace.commands == "environments":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )
        display_environments(
            mapping["environment"],
            all_versions=namespace.all,
            commands_only=namespace.with_commands
        )

    elif namespace.commands == "search":
        requirement = Requirement(namespace.requirement)
        mapping = wiz.definition.search(
            requirement, registries,
            max_depth=namespace.definition_search_depth
        )

        if len(mapping):
            display_environments(
                mapping["environment"], all_versions=namespace.all
            )
        else:
            print("No results found.")

    elif namespace.commands in ["view", "load"]:
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        requirements = map(Requirement, namespace.requirements)

        try:
            environments = wiz.environment.compute(
                requirements, mapping["environment"]
            )
            environment = wiz.environment.resolve(environments)

            if namespace.commands == "view":
                display_environment(environment)

            elif namespace.commands == "load":
                wiz.spawn.shell(environment["data"])

            # elif namespace.commands == "run":
            #     if namespace.command not in result.get("command", []):
            #         raise wiz.exception.CommandError(namespace.command)
            #
            #     command = result["command"][namespace.command]
            #     wiz.spawn.execute(command, result["data"])

        except wiz.exception.WizError:
            logger.error(
                "Impossible to resolve the environment graph.",
                traceback=True
            )


def display_environments(
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
    line = _format_row(["Definition", "Version", "Variants", "Description"])
    print("\n" + line)
    print("+".join(["-"*30]*4) + "-"*30)

    def _display(_environment):
        """Display information about *environment*."""
        if commands_only and _environment.get("command") is None:
            return

        variants = [
            _env.get("identifier") for _env in _environment.get("variant", [])
        ]

        _line = _format_row([
            _environment.identifier,
            _environment.version,
            ", ".join(variants),
            _environment.description
        ])
        print(_line)

    for identifier, version_mapping in sorted(environment_mapping.items()):
        sorted_environments = sorted(
            version_mapping.values(), key=lambda _env: _env.version,
            reverse=True
        )

        if all_versions:
            for environment in sorted_environments:
                _display(environment)
        else:
            environment = sorted_environments[0]
            _display(environment)

    print()


def display_environment(environment):
    """Display the content of the *environment* mapping."""
    commands = sorted(environment.get("command", {}).keys())
    if len(commands) > 0:
        print("\n Commands")
        print("-"*120)
        print(", ".join(commands))
        print()

    line = _format_row(["Environment variable", "Value"], width=40)
    print("\n" + line)
    print("+".join(["-"*40]*2) + "-"*40)

    def _compute_value(name, value):
        """Compute value to display."""
        if name == "DISPLAY":
            return [value]
        return value.split(os.pathsep)

    data_mapping = environment.get("data", {})
    for key in sorted(data_mapping.keys()):
        for _key, _value in itertools.izip_longest(
            [key], _compute_value(key, data_mapping[key])
        ):
            line = _format_row([_key or "", _value], width=40)
            print(line)

    print()


def _format_row(elements, width=30):
    """Return formatted line of *elements* in columns.

    *width* indicates the size of each column (except the last one).

    """
    line = ""
    number_elements = len(elements)

    for index in range(number_elements):
        element = " {} ".format(elements[index])

        if index == number_elements - 1:
            line += element
        elif len(element) > width:
            line += "{}...|".format(element[:width-3])
        else:
            line += "{}{}|".format(element, " " * (width-len(element)))

    return line

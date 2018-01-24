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
            "Do not attempt to discover environment definitions from current "
            "working directory within project."
        ),
        action="store_true"
    )

    parser.add_argument(
        "-dsd", "--definition-search-depth",
        help="Maximum depth to recursively search for environment definitions.",
        type=int
    )

    subparsers = parser.add_subparsers(
        title="Commands",
        dest="commands"
    )

    registries_parser= subparsers.add_parser(
        "registries",
        help="List all available registries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    registries_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for environment definitions.",
        default=wiz.registry.get_defaults()
    )

    definitions_parser = subparsers.add_parser(
        "definitions",
        help="List all available environment definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    definitions_parser.add_argument(
        "--all",
        help="Return all versions of the available definitions.",
        action="store_true"
    )

    definitions_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for environment definitions.",
        default=wiz.registry.get_defaults()
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search an environment definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    search_parser.add_argument(
        "--all",
        help="Return all versions of the available definitions.",
        action="store_true"
    )

    search_parser.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for environment definitions.",
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
        help="Search paths for environment definitions.",
        default=wiz.registry.get_defaults()
    )

    view_subparsers.add_argument(
        "requirements",
        nargs="+",
        help="Definition requirements required."
    )

    load_subparsers = subparsers.add_parser(
        "load",
        help="Spawn shell with resolved environment from requirements.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    load_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for environment definitions.",
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
        help="Indicate definition requirements required."
    )

    run_subparsers.add_argument(
        "-dsp", "--definition-search-paths",
        nargs="+",
        metavar="PATH",
        help="Search paths for environment definitions.",
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

    elif namespace.commands == "definitions":
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )
        display_definitions(mapping, all_versions=namespace.all)

    elif namespace.commands == "search":
        requirement = Requirement(namespace.requirement)
        mapping = wiz.definition.search(
            requirement, registries,
            max_depth=namespace.definition_search_depth
        )

        if len(mapping):
            display_definitions(mapping, all_versions=namespace.all)
        else:
            print("No results found.")

    elif namespace.commands in ["view", "load", "run"]:
        mapping = wiz.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        requirements = map(Requirement, namespace.requirements)

        try:
            definitions = wiz.environment.resolve(requirements, mapping)
            result = wiz.environment.extract_mapping(definitions)

            if namespace.commands == "view":
                display_environment(result["environ"])

            elif namespace.commands == "load":
                wiz.spawn.shell(result["environ"])

            elif namespace.commands == "run":
                if namespace.command not in result.get("command", []):
                    raise wiz.exception.CommandError(namespace.command)

                executable = result["command"][namespace.command]
                wiz.spawn.command(executable, result["environ"])

        except wiz.exception.WizError:
            logger.error(
                "Impossible to resolve the environment graph.",
                traceback=True
            )


def display_definitions(definition_mapping, all_versions=False):
    """Display the environment definitions stored in *definition_mapping*.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier.

    *all_versions* indicate whether all versions from the definitions must be
    returned. If not, only the latest version of each definition identifier is
    displayed.

    """
    line = _format_row(["Definition", "Version", "Variants", "Description"])
    print("\n" + line)
    print("+".join(["-"*30]*4) + "-"*30)

    for identifier, version_mapping in sorted(definition_mapping.items()):
        sorted_definitions = sorted(
            version_mapping.values(),
            key=lambda _definition: _definition.version,
            reverse=True
        )

        if all_versions:
            for definition in sorted_definitions:
                variant_mapping = definition.get("variant", {})
                line = _format_row([
                    definition.identifier,
                    definition.version,
                    ", ".join(variant_mapping.keys()),
                    definition.description
                ])
                print(line)

        else:
            definition = sorted_definitions[0]
            variant_mapping = definition.get("variant", {})
            line = _format_row([
                definition.identifier,
                definition.version,
                ", ".join(variant_mapping.keys()),
                definition.description
            ])
            print(line)

    print()


def display_environment(environment):
    """Display the content of the *environment* mapping."""
    line = _format_row(["Environment variable", "Value"], width=40)
    print("\n" + line)
    print("+".join(["-"*40]*2) + "-"*40)

    def _compute_value(name, value):
        """Compute value to display."""
        if name == "DISPLAY":
            return [value]
        return value.split(os.pathsep)

    for key in sorted(environment.keys()):
        for _key, _value in itertools.izip_longest(
            [key], _compute_value(key, environment[key])
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

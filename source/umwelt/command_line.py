# :coding: utf-8

from __future__ import print_function
import argparse
import os
import itertools

import mlog
from packaging.requirements import Requirement

import umwelt.definition
import umwelt.environment
import umwelt.shell


def construct_parser():
    """Return argument parser."""
    parser = argparse.ArgumentParser(
        prog="umwelt",
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
        "--no-local", help="Skip local registry.",
        action="store_true"
    )

    parser.add_argument(
        "--no-cwd", help=(
            "Do not discover registry from current working directory."
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

    registries_parser = subparsers.add_parser(
        "registries", help="List all available registers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    registries_parser.add_argument(
        "--registries", nargs="+", metavar="PATH",
        help=(
            "Indicate registries containing all available "
            "environment definitions."
        ),
        default=default_registries()
    )

    definitions_parser = subparsers.add_parser(
        "definitions", help="List all available environment definitions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    definitions_parser.add_argument(
        "--all", help="Return all versions of the available definitions.",
        action="store_true"
    )

    definitions_parser.add_argument(
        "--registries", nargs="+", metavar="PATH",
        help=(
            "Indicate registries containing all available "
            "environment definitions."
        ),
        default=default_registries()
    )

    search_parser = subparsers.add_parser(
        "search", help="Search an environment definition.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    search_parser.add_argument(
        "--all", help="Return all versions of the available definitions.",
        action="store_true"
    )

    search_parser.add_argument(
        "--registries", nargs="+", metavar="PATH",
        help=(
            "Indicate registries containing all available "
            "environment definitions."
        ),
        default=default_registries()
    )

    search_parser.add_argument(
        "requirement", help="Definition requirement to search."
    )

    view_subparsers = subparsers.add_parser(
        "view", help="View combined environment from definition(s).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    view_subparsers.add_argument(
        "--registries", nargs="+", metavar="PATH",
        help=(
            "Indicate registries containing all available "
            "environment definitions."
        ),
        default=default_registries()
    )

    view_subparsers.add_argument(
        "requirements", nargs="+", help="Definition requirements required."
    )

    load_subparsers = subparsers.add_parser(
        "load", help="Load combined environment from definition(s).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    load_subparsers.add_argument(
        "--registries", nargs="+", metavar="PATH",
        help=(
            "Indicate registries containing all available "
            "environment definitions."
        ),
        default=default_registries()
    )

    load_subparsers.add_argument(
        "requirements", nargs="+", help="Definition requirements required."
    )

    return parser


def main(arguments=None):
    """Umwelt command line interface."""
    if arguments is None:
        arguments = []

    mlog.configure()
    logger = mlog.Logger(__name__ + ".main")

    # Process arguments.
    parser = construct_parser()
    namespace = parser.parse_args(arguments)

    mlog.root.handlers["stderr"].filterer.filterers[0].min = (
        namespace.verbosity
    )

    # Fetch all registries
    registries = fetch_registries(
        namespace.registries,
        include_local=not namespace.no_local,
        include_working_directory=not namespace.no_cwd
    )
    logger.debug("Registries: " + ", ".join(registries))

    # Process requested operation.
    if namespace.commands == "registries":
        print("\n".join(registries))

    elif namespace.commands == "definitions":
        mapping = umwelt.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )
        display_definitions(mapping, all_versions=namespace.all)

    elif namespace.commands == "search":
        requirement = Requirement(namespace.requirement)
        mapping = umwelt.definition.search(
            requirement,
            registries,
            max_depth=namespace.definition_search_depth
        )

        if not len(mapping):
            print("No results found.")
        else:
            display_definitions(mapping, all_versions=namespace.all)

    elif namespace.commands == "view":
        mapping = umwelt.definition.fetch(
            registries,
            max_depth=namespace.definition_search_depth
        )

        requirements = [
            Requirement(requirement) for requirement in namespace.requirements
        ]

        try:
            environment = umwelt.environment.resolve(
                requirements, mapping
            )

        except RuntimeError:
            logger.error(
                "Impossible to resolve the environment tree.",
                traceback=True
            )

        else:
            display_environment(environment)

    elif namespace.commands == "load":
        mapping = umwelt.definition.fetch(
            registries, max_depth=namespace.definition_search_depth
        )

        requirements = [
            Requirement(requirement) for requirement in namespace.requirements
        ]

        try:
            environment = umwelt.environment.resolve(
                requirements, mapping
            )

        except RuntimeError:
            logger.error(
                "Impossible to resolve the environment tree.",
                traceback=True
            )

        else:
            umwelt.shell.spawn_shell(environment)


def local_registry():
    """Return the local registry if available."""
    registry_path = os.path.join(
        os.path.expanduser("~"), ".registry"
    )

    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path


def default_registries():
    """Return the default registries."""
    return [
        os.path.join(os.sep, "mill3d", "server", "REGISTRY"),
        # os.path.join(os.sep, "jobs", "ads", ".registry")
    ]


def fetch_registries(paths, include_local=True, include_working_directory=True):
    """Fetch all registries from *paths*.

    *include_local* indicate whether the local registry should be included.

    *include_local* indicate whether the current working directory should be
     parsed to discover a registry.

    """
    registries = []

    for path in paths:
        if not os.path.isdir(path):
            raise IOError("The registry must be a directory: {}".format(path))
        if not os.access(path, os.R_OK):
            raise IOError("The registry must be readable: {}".format(path))

        registries.append(path)

    if include_working_directory:
        registry_path = discover_registry_from_path(os.getcwd())
        if registry_path:
            registries.append(registry_path)

    registry_path = local_registry()
    if registry_path and include_local:
        registries.append(registry_path)

    registries.reverse()
    return registries


def discover_registry_from_path(path):
    """Return registry from *path* if available under the folder structure.

    The registry path should be a ".registry" folder within *path*.

    Return the registry path discovered, or None if the register is not found
    or not accessible.

    .. note::

        No registry will be fetched if *path* is not under `/jobs/ads`.

    """
    path = os.path.abspath(path)

    # Only discover the registry if the top level hierarchy is /jobs/ads.
    prefix = os.path.join(os.sep, "jobs", "ads")
    if not path.startswith(prefix):
        return

    registry_path = os.path.join(path, ".registry")
    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path


def display_definitions(definition_mapping, all_versions=False):
    """Display the environment definitions stored in *definition_mapping*.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier.

    *all_versions* indicate whether all versions from the definitions must be
    returned. If not, only the latest version of each definition identifier is
    displayed.

    """
    line = format_row(["Definition", "Version", "Variants", "Description"])
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
                line = format_row([
                    definition.identifier,
                    definition.version,
                    ", ".join(variant_mapping.keys()),
                    definition.description
                ])
                print(line)

        else:
            definition = sorted_definitions[0]
            variant_mapping = definition.get("variant", {})
            line = format_row([
                definition.identifier,
                definition.version,
                ", ".join(variant_mapping.keys()),
                definition.description
            ])
            print(line)

    print()


def display_environment(environment):
    """Display the content of the *environment* mapping."""
    line = format_row(["Environment variable", "Value"], width=40)
    print("\n" + line)
    print("+".join(["-"*40]*2) + "-"*40)

    for key in sorted(environment.keys()):
        for _key, value in itertools.izip_longest(
            [key], split_environment_variable_value(key, environment[key])
        ):
            line = format_row([_key or "", value],  width=40)
            print(line)

    print()


def split_environment_variable_value(name, value):
    """Return *value* for environment variable *name* as a list.

    Example::

        >>> split_environment_variable_value("name", "value1:value2:value3")
        ["value1", "value2", "value3"]

        >>> split_environment_variable_value("name", "value1")
        ["value1"]

    Depending on the *name*, some value should keep the ":" (e.g. "DISPLAY")

    """
    if name == "DISPLAY":
        return [value]
    return value.split(os.pathsep)


def format_row(elements, width=30):
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

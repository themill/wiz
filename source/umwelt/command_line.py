# :coding: utf-8

import argparse
import os

import mlog
from packaging.requirements import Requirement
from packaging.version import Version

import umwelt.definition


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
        "--no-pwd", help="Do not discover registry from current path.",
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
        "definition", help="Definition specifier"
    )

    load_subparsers = subparsers.add_parser(
        "load", description="Load an environment.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    load_subparsers.add_argument(
        "definition", help="Definition specifier"
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
        namespace.registries, include_local=not namespace.no_local
    )
    logger.debug("Registries: " + ", ".join(registries))

    # Process requested operation.
    if namespace.commands == "registries":
        print "\n".join(registries)

    elif namespace.commands == "definitions":
        mapping = fetch_definition_mapping(
            registries, max_depth=namespace.definition_search_depth
        )
        display_definitions(mapping, all_versions=namespace.all)

    elif namespace.commands == "search":
        mapping = search_definitions(
            namespace.definition,
            registries, max_depth=namespace.definition_search_depth
        )
        if not len(mapping):
            print "No results found."
        else:
            display_definitions(mapping, all_versions=namespace.all)


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
        os.path.join(os.sep, "jobs", "ads", ".registry")
    ]


def fetch_registries(paths, include_local=True):
    """Fetch all registries from *paths*.

    *include_local* indicate whether the local registry should be included.

    """
    registries = []

    for path in paths:
        if not os.path.isdir(path):
            raise IOError("The registry must be a directory: {}".format(path))
        if not os.access(path, os.R_OK):
            raise IOError("The registry must be readable: {}".format(path))

        registries.append(path)

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


def fetch_definition_mapping(paths, max_depth=None):
    """Return mapping from all environment definitions available under *paths*.

    :func:`~umwelt.definition.discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    mapping = dict()

    for definition in umwelt.definition.discover(paths, max_depth=max_depth):
        mapping.setdefault(definition.identifier, [])
        mapping[definition.identifier].append(definition)

    return mapping


def search_definitions(definition, paths, max_depth=None):
    """Return mapping from environment definitions matching *requirement*.

    *definition* can indicate a definition specifier which must adhere to
    `PEP 508 <https://www.python.org/dev/peps/pep-0508>`_.

    :exc:`packaging.requirements.InvalidRequirement` is raised if the
    requirement specifier is incorrect.

    :func:`~umwelt.definition.discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".search_definitions")
    logger.info(
        "Search environment definition definitions matching {0!r}"
        .format(definition)
    )

    mapping = dict()

    for definition in umwelt.definition.discover(paths, max_depth=max_depth):
        requirement = Requirement(definition)
        if (
            requirement.name in definition.identifier or
            requirement.name in definition.description
        ):
            if Version(definition.version) in requirement.specifier:
                mapping.setdefault(definition.identifier, [])
                mapping[definition.identifier].append(definition)

    return mapping


def display_definitions(definition_mapping, all_versions=False):
    """Display the environment definitions stored in *definition_mapping*.

    *all_versions* indicate whether all versions from the definitions must be
    returned. If not, only the latest version of each definition identifier is
    displayed.

    """
    for identifier, definitions in definition_mapping.items():
        sorted_definitions = sorted(
            definitions, key=lambda d: d.version, reverse=True
        )

        if all_versions:
            for definition in sorted_definitions:
                print (
                    "{0[identifier]} [{0[version]}]\t\t\t{0[description]}"
                    .format(definition)
                )

        else:
            print (
                "{0[identifier]} [{0[version]}]\t\t\t{0[description]}"
                .format(sorted_definitions[0])
            )

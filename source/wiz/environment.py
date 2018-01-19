# :coding: utf-8

import os
import re

import mlog

import wiz.definition
import wiz.graph


def resolve(requirements, definition_mapping, environ_mapping=None):
    """Return resolved environment mapping corresponding to *requirements*.

    *requirements* should be a list of
    class:`packaging.requirements.Requirement` instances.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    Raise :exc:`RuntimeError` if the graph cannot be built.

    """
    logger = mlog.Logger(__name__ + ".resolve")
    logger.info(
        "Resolve environment: {}".format(
            ", ".join([str(requirement) for requirement in requirements])
        )
    )

    # Compute initial environment mapping to augment.
    environ_mapping = initiate(environ_mapping)

    # Create a graph with all required definition versions.
    graph = wiz.graph.Graph(definition_mapping)
    graph.update_from_requirements(requirements)

    # Ensure that only one version is required for each definition in the graph.
    # Otherwise attempt to resolve the possible conflicts.
    wiz.graph.resolve_conflicts(graph, definition_mapping)

    # Extract all definition versions from the graph from the less important to
    # the most important. The most important being the highest definition
    # versions in the graph.
    definitions = wiz.graph.extract_ordered_definitions(graph)

    # Combine all environments from each definition version extracted with the
    # initial environment.
    return extract(definitions, environ_mapping)


def extract(definitions, environ_mapping=None):
    """Return environment mapping extracted from *definitions*.

    *definitions* should be a list of :class:`~wiz.definition.Definition`
    instances. it should be ordered from the less important to the most
    important so that the later are prioritized over the first.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    def _combine(definition1, definition2):
        """Return intermediate definition combining both environments"""
        definition2["environ"] = wiz.definition.extract_environment(
            definition1, definition2
        )
        return definition2

    combined_definition = reduce(
        _combine, definitions, dict(environ=environ_mapping)
    )

    # Clean all values from possible key references.
    environ = combined_definition.get("environ", {})
    for key, value in environ.items():
        environ[key] = re.sub(":?\${{{}}}:?".format(key), lambda x: "", value)

    return environ


def initiate(environ_mapping=None):
    """Return the initiate environment to augment.

    The initial environment contains basic variables from the external
    environment that can be used in the environment definitions, such as
    the *USER* or the *HOME* variables.

    The other variable added are:

    * DISPLAY:
        This variable is necessary to open user interface within the current
        X display name.

    * PATH:
        This variable is initialised with default values to have access to the
        basic UNIX commands.

    *environ_mapping* can be a custom environment mapping which will be added
    to the initial environment.

    """
    environ = {
        "USER": os.environ.get("USER"),
        "HOME": os.environ.get("HOME"),
        "DISPLAY": os.environ.get("DISPLAY"),
        "PATH": os.pathsep.join([
            "/usr/get_local/sbin",
            "/usr/get_local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }

    if environ_mapping is not None:
        environ.update(**environ_mapping)

    return environ

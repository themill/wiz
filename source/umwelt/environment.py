# :coding: utf-8

import os

import mlog

import umwelt.definition
import umwelt.graph


def resolve_environment(requirements, definition_mapping):
    """Return resolved environment mapping corresponding to *requirements*.

    *requirements* should be a list of
    class:`packaging.requirements.Requirement` instances.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    Raise :exc:`RuntimeError` if the graph cannot be built.

    """
    logger = mlog.Logger(__name__ + ".resolve_environment")
    logger.info(
        "Resolve environment: {}".format(
            ", ".join([str(requirement) for requirement in requirements])
        )
    )

    graph = umwelt.graph.Graph(definition_mapping)
    graph.update_from_requirements(requirements)

    umwelt.graph.resolve_conflicts(graph, definition_mapping)

    definitions = umwelt.graph.extract_ordered_definitions(graph)

    environ = reduce(
        lambda def1, def2: umwelt.definition.combine(def1, def2),
        definitions, {}
    ).get("data", {})

    serialize_environment_values(environ)
    return environ


def serialize_environment_values(environment):
    """Mutate *environment* mapping to serialize its values."""
    for key in environment.keys():
        value = environment[key]

        if isinstance(value, list):
            environment[key] = os.pathsep.join(value)
        else:
            environment[key] = str(value)

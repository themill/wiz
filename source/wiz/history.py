# :coding: utf-8

import os
import platform
import datetime


#: Indicate whether the history should be recorded.
_IS_HISTORY_RECORDED = False

#: Mapping containing the entire context resolution history report.
_HISTORY = {
    "user": os.environ.get("USER"),
    "hostname": platform.node(),
    "time": datetime.datetime.now().isoformat(),
    "command": None,
    "actions": []
}


def get():
    """Return mapping of recorded history."""
    return _HISTORY


def start_recording(command=None):
    """Start recording the context resolution actions.

    *command* can indicate the command which is being run via the command line.

    """
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = True

    if command is not None:
        global _HISTORY
        _HISTORY["command"] = command


def stop_recording():
    """Stop recording the context resolution actions."""
    global _IS_HISTORY_RECORDED
    _IS_HISTORY_RECORDED = False


def _record_action(action_identifier, **kwargs):
    """Add an action to the global history mapping.

    *action_identifier* should be the identifier of an action.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    if not _IS_HISTORY_RECORDED:
        return

    action = {"identifier": action_identifier}
    action.update(**kwargs)

    global _HISTORY
    _HISTORY["actions"].append(action)


def record_system_identification(mapping):
    """Record system *mapping* identification.

    *mapping* should be in the form of::

        {
            "platform": "linux",
            "arch": "x86_64",
            "os": {
                "name": "centos",
                "version": "7.3.161"
            }
        }

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action(
        "IDENTIFY_SYSTEM",
        system=mapping,
    )


def record_definitions_retrieval(paths, max_depth, mapping):
    """Record *definition_mapping* fetched from *registries* to the history.

    *paths* should be the path to each registry visited.

    *max_depth* could be the maximum level of research within registry folders.

    *mapping* should be a mapping regrouping all available definitions.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action(
        "FETCH_DEFINITIONS",
        registries=paths,
        max_depth=max_depth,
        definition_mapping=mapping
    )


def record_graph_creation(graph):
    """Record the creation of a new *graph* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action("CREATE_GRAPH", graph=graph)


def record_priority_computation(graph, priority_mapping):
    """Record computation of *graph* priority mapping to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action(
        "CREATE_PRIORITY_MAPPING",
        graph_identifier=graph.identifier,
        priority_mapping=priority_mapping
    )


def record_node_creation(graph, node_identifier):
    """Record the creation of a new graph *node* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *node_identifier* should be the identifier of a node in the graph.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action("CREATE_NODE", graph=graph, node_identifier=node_identifier)


def record_node_removal(graph, node_identifier):
    """Record the removal of a *node* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *node_identifier* should be the identifier of a node in the graph.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action("REMOVE_NODE", graph=graph, node_identifier=node_identifier)


def record_variants_removal(graph):
    """Record the removal of variants from *graph* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action("REMOVE_VARIANTS", graph=graph)


def record_link_creation(graph, parent_identifier, child_identifier, weight):
    """Record the creation of a link between two nodes to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *parent_identifier* and *child_identifier* should be the identifiers of
    nodes in the graph.

    *weight* indicate a the weight of the link.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action(
        "CREATE_LINK",
        graph=graph,
        parent_identifier=parent_identifier,
        child_identifier=child_identifier,
        weight=weight
    )


def record_conflicts_identification(graph, node_identifiers):
    """Record the identification of conflicted nodes in *graph* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *node_identifiers* should be a identifier list of nodes in the graph.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action(
        "IDENTIFY_CONFLICTS",
        graph=graph,
        node_identifiers=node_identifiers,
    )


def record_variants_identification(graph, variant_groups):
    """Record the identification of variant nodes in *graph* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *variant_groups* should be a list of variants identifier node lists for
    nodes in the graph.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action(
        "IDENTIFY_VARIANTS",
        graph=graph,
        variant_groups=variant_groups,
    )


def record_package_extraction(graph, packages):
    """Record the extraction of *packages* from *graph* to the history.

    *graph* must be an instance of :class:`wiz.graph.Graph`.

    *packages* must be a list of :class:`~wiz.package.Package` instances.

    .. warning::

        This operation will be discarded if the history is not being
        :func:`recorded <start_recording>`.

    """
    _record_action("EXTRACT_PACKAGES", graph=graph, packages=packages)

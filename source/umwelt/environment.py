# :coding: utf-8

import os
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import mlog
import collections

import umwelt.definition


#: Node leaf composing the :class:`DependencyTree`.
Node = collections.namedtuple(
    "Node", ["identifier", "definition", "requirement", "parent"]
)


def resolve(requirements, definition_mapping):
    """Return resolved environment mapping corresponding to *requirements*.

    *requirements* should be a list of
    class:`packaging.requirements.Requirement` instances.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    Raise :exc:`RuntimeError` if the tree cannot be built.

    :exc:`packaging.requirements.InvalidRequirement` is raised if a
    requirement specifier is incorrect.

    """
    logger = mlog.Logger(__name__ + ".resolve")
    logger.info(
        "Resolve environment: {!r}".format(requirements)
    )

    graph = Graph()
    for requirement in requirements:
        graph.add_node(requirement, definition_mapping)

    definitions = sorted_definitions(graph)

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


def sorted_definitions(graph):
    """Return list of definitions topologically sorted from *graph*.
    """
    logger = mlog.Logger(__name__ + ".sorted_definitions")

    queue = Queue()
    indegree_mapping = dict()

    for identifier in graph.identifiers:
        indegree_mapping[identifier] = graph.indegree(identifier)

        # Queue all node identifiers which have no parent
        if indegree_mapping[identifier] == 0:
            queue.put(identifier)

    definitions = []

    while not queue.empty():
        identifier = queue.get()

        definitions.append(
            graph.definition(identifier)
        )

        for identifier in graph.adjacents(identifier):
            indegree_mapping[identifier] = indegree_mapping[identifier] - 1

            if indegree_mapping[identifier] == 0:
                queue.put(identifier)

    if len(definitions) != len(graph.identifiers):
        raise RuntimeError(
            "A cycle has been detected in the dependency graph"
        )

    logger.debug(
        "Topologically sorted definitions: {}".format(
            [d.identifier for d in definitions]
        )
    )

    return definitions


class Graph(object):
    """Dependency Graph.
    """

    def __init__(self):
        """Initialise Graph."""
        self._logger = mlog.Logger(__name__ + ".EnvironmentGraph")

        # Record the weight of each link in the graph.
        self._links = dict()

        # Record node leaf created per definition identifier.
        self._nodes = dict()

    @property
    def identifiers(self):
        """Return all environment identifiers in the tree."""
        return self._nodes.keys()

    def definition(self, identifier):
        """Return definition from *identifier*."""
        return self._nodes[identifier].definition

    def indegree(self, identifier):
        """Return indegree value for *identifier*."""
        indegree = 0

        for parent_identifier in self._nodes.keys():
            if self._links.get(parent_identifier, {}).get(identifier, 0) > 0:
                indegree = indegree + 1

        return indegree

    def adjacents(self, identifier):
        """Return list of adjacent node identifiers for *identifier*."""
        identifiers = []
        for _identifier in self._nodes.keys():
            if self._links.get(identifier, {}).get(_identifier, 0) > 0:
                identifiers.append(_identifier)

        return identifiers

    def add_node(self, requirement, definition_mapping, parent=None):
        """Recursively create dependency node(s) from *definition_requirement*.

        *requirement* is an instance of
        :class:`packaging.requirements.Requirement`.

        *definition_mapping* is a mapping regrouping all available environment
        definition associated with their unique identifier. It is used to
        resolve dependent definition specifiers.

        *parent* can indicate a parent :class:`~umwelt.definition.Definition`.

        Raise :exc:`RuntimeError` is a version conflict is detected.

        """
        self._logger.debug("Add node for '{}'".format(requirement))

        definition = umwelt.definition.get(requirement, definition_mapping)

        # Create node from definition.
        node = Node(
            definition.identifier,
            definition,
            requirement,
            parent
        )

        # Check is a node with the same definition identifier is in the graph.
        if node.identifier in self._nodes.keys():
            _node = self._nodes[node.identifier]

            # If the definition identifier has already been used in the graph
            # with a specifier incompatible with the current definition's
            # version, raise an error.
            if not self._is_compatible(node, _node):
                raise RuntimeError(
                    "A version conflict has been detected for '{id!r}'\n"
                    " - {node1}\n"
                    " - {node2}\n".format(
                        id=node.requirement,
                        node1=self._display_node(node),
                        node2=self._display_node(_node),
                    )
                )

            # Otherwise update the node with the new version if necessary.
            if (
                node.definition.version != _node.definition.version and
                _node.definition.version not in node.requirement.specifier
            ):
                self._nodes[node.identifier] = node

                self._logger.debug(
                    "Replace {identifier!r}: {version1} -> {version2}".format(
                        identifier=node.identifier,
                        version1=_node.definition.version,
                        version2=node.definition.version
                    )
                )

        # Add node to the graph if no other node with the same definition
        # identifier is found.
        else:
            self._nodes[node.identifier] = node
            self._logger.debug(
                "Create {0.identifier!r}: {0.definition.version}".format(
                    self._nodes[node.identifier])
            )

        # Add a dependency link if necessary.
        if parent is not None:
            self.add_link(node.identifier, parent.identifier)

        # Recursively resolve all dependencies.
        dependencies = definition.get("dependency", [])
        for dependency_requirement in dependencies:
            self.add_node(
                dependency_requirement, definition_mapping, parent=definition
            )

    def _is_compatible(self, node1, node2):
        """Return whether *node1* and *node2* are compatible."""

        # Nodes are not compatible if both definition versions are not
        # compatible with at least one of the specifier.
        if (
            node1.definition.version not in node2.requirement.specifier and
            node2.definition.version not in node1.requirement.specifier
        ):
            return False

        # Nodes are not compatible if different variants were requested.
        if node1.requirement.extras != node2.requirement.extras:
            return False

        return True

    def _display_node(self, node):
        """Return formatted identifier for :class:`Node` instance*."""
        message = "{}".format(node.requirement)

        if node.parent is not None:
            message += " [from {!r}]".format(node.parent.identifier)

        return message

    def add_link(self, identifier, parent_identifier, weight=1):
        """Add *definition* environment as a dependency link of *parent*.

        *identifier* is the identifier of the environment which is added to the
        dependency graph.

        *parent_identifier* is the identifier of the targeted environment which
        must be linked to the new *identifier*.

        *weight* is a number which indicate the importance of the dependency
        link. default is 1.

        Raise :exc:`RuntimeError` is *definition* identifier has already be
        set for this *parent*.

        """
        self._logger.debug(
            "Add dependency link from {parent!r} to {child!r}".format(
                parent=parent_identifier, child=identifier
            )
        )

        self._links.setdefault(parent_identifier, {})

        if identifier in self._links[parent_identifier].keys():
            raise RuntimeError(
                "The definition identified by {!r} is requested twice for the "
                "same parent [{!r}]".format(
                    identifier, parent_identifier
                )
            )

        self._links[parent_identifier][identifier] = weight

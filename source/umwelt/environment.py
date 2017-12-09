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

    *requirements* indicates a list of definition requirements which must
    adhere to `PEP 508 <https://www.python.org/dev/peps/pep-0508>`_.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    Raise :exc:`RuntimeError` if the tree cannot be built.

    :exc:`packaging.requirements.InvalidRequirement` is raised if a
    requirement specifier is incorrect.

    """
    logger = mlog.Logger(__name__ + ".create_tree")
    logger.info(
        "Resolve environment: {!r}".format(requirements)
    )

    graph = Graph()
    for requirement in requirements:
        graph.add_node(requirement, definition_mapping)

    definitions = sorted_definitions(graph)

    environ = reduce(
        lambda def1, def2: combined_data(def1, def2), definitions, {}
    ).get("data", {})

    serialize_environment_values(environ)
    return environ


def sorted_definitions(graph):
    """Return list of definitions topologically sorted from *graph*.
    """
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

    return definitions


def combined_data(definition1, definition2):
    """Return combined environment data from *definition1* and *definition2*"""
    definition = {"data": dict()}

    # Extract environment from definitions
    environment1 = definition1.get("data", {})
    environment2 = definition2.get("data", {})

    for key in set(environment1.keys() + environment2.keys()):
        value1 = environment1.get(key)
        value2 = environment2.get(key)

        # The keyword must not have a value in the two environment, unless if
        # it is a list that can be combined.
        if value1 is not None and value2 is not None:
            if not isinstance(value1, list) or not isinstance(value2, list):
                raise RuntimeError(
                    "Overriding environment variable per definition is "
                    "forbidden\n"
                    " - {definition1}: {key}={value1!r}\n"
                    " - {definition2}: {key}={value2!r}\n".format(
                        key=key, value1=value1, value2=value2,
                        definition1=definition1.identifier,
                        definition2=definition2.identifier,
                    )
                )

            definition["data"][key] = value1 + value2

        # Otherwise simply set the valid value
        else:
            definition["data"][key] = value1 or value2

    return definition


def serialize_environment_values(environment):
    """Mutate *environment* mapping to serialize its values."""
    for key in environment.keys():
        value = environment[key]

        if isinstance(value, list):
            environment[key] = os.pathsep.join(value)
        else:
            environment[key] = str(value)


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

        *requirement* indicates a definition requirement which must
        adhere to `PEP 508 <https://www.python.org/dev/peps/pep-0508>`_.

        *definition_mapping* is a mapping regrouping all available environment
        definition associated with their unique identifier. It is used to
        resolve dependent definition specifiers.

        *parent* can indicate a parent :class:`~umwelt.definition.Definition`.

        Raise :exc:`RuntimeError` is a version conflict is detected.

        """
        self._logger.debug("Add node for '{}'".format(requirement))

        definition = umwelt.definition.get(requirement, definition_mapping)

        # Create node from definition.
        node = Node(definition.identifier, definition, requirement, parent)

        # Check is a node with the same definition identifier is in the graph.
        if node.identifier in self._nodes.keys():
            _node = self._nodes[node.identifier]

            # If the definition identifier has already been used in the graph
            # with a specifier incompatible with the current definition's
            # version, raise an error.
            if node.definition.version not in _node.requirement.specifier:
                raise RuntimeError(
                    "A version conflict has been detected for '{id!r}'\n"
                    " - {node1}\n"
                    " - {node2}\n".format(
                        id=node.requirement,
                        node1=self._display_node(node),
                        node2=self._display_node(_node),
                    )
                )

            # Otherwise update the node with the highest version if necessary.
            updated = max(node, _node, key=lambda n: n.definition.version)

            if updated.definition.version != _node.requirement.specifier:
                self._nodes[node.identifier] = updated

                self._logger.debug(
                    "Replace {identifier!r}: {version1} -> {version2}".format(
                        identifier=node.identifier,
                        version1=_node.definition.version,
                        version2=updated.definition.version
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

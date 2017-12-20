# :coding: utf-8

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import mlog
import collections

import umwelt.definition


#: Node leaf composing the :class:`Graph`.
_GraphNode = collections.namedtuple(
    "GraphNode", [
        "identifier", "definition", "requirement", "parent_identifier"
    ]
)


class Graph(object):
    """Dependency Graph.

    A dependency graph can be created from required environment definitions.
    All possible definition versions will be created.

    Let's consider the following example::

        >>> graph = Graph(...)
        >>> graph.update_from_requirement("envA >= 0.1.0")

    The following nodes will be added to the graph::

        envA==0.2.0
        envB==0.1.0 [required by 'envA==0.2.0' with 'envB<0.2.0']
        envC==0.3.2 [required by 'envA==0.2.0' with 'envC>=0.3.2,<1']
        envD==0.1.1 [required by 'envB==0.1.0' with 'envD>=0.1.0']
        envD==0.1.0 [required by 'envC==0.3.2' with 'envD==0.1.0']
        envE==2.3.0 [required by 'envD==0.1.1' with 'envE>=2']
        envF==1.0.0 [required by 'envB==0.1.0' with 'envF>=1']
        envF==0.2.0 [required by 'envE==2.3.0' with 'envF>=0.2']

    However, the final environment cannot be deducted from such a tree as it
    contains several errors

    """

    def __init__(self, definition_mapping):
        """Initialise Graph.

        *definition_mapping* is a mapping regrouping all available environment
        definition associated with their unique identifier. It is used to
        resolve dependent definition specifiers.

        """
        self._logger = mlog.Logger(__name__ + ".Graph")

        # All available definitions.
        self._definition_mapping = definition_mapping

        # Set of required nodes per common definition identifier.
        self._required_definitions = {}

        # All required nodes per node identifier.
        self._nodes = {}

        # All in-coming and out-coming links per node identifier.
        self._links_from = dict()
        self._links_to = dict()

    def dependencies_number(self, identifier):
        """Return number of dependencies for node *identifier*."""
        return len(self._links_from.get(identifier, []))

    def parents(self, identifier):
        """Yield parent node identifiers for node *identifier*."""
        for identifier in self._links_to.get(identifier, []):
            # Ignore node if it has been previously removed.
            if self._nodes.get(identifier) is not None:
                yield identifier

    def update_from_requirement(self, requirement, parent_identifier=None):
        """Recursively create nodes from *requirement*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *parent_identifier* can indicate the identifier of a parent node.

        """
        self._logger.debug("Update from requirement: {}".format(requirement))

        definition = umwelt.definition.get(
            requirement, self._definition_mapping
        )

        identifier = "{definition}=={version}".format(
            definition=definition.identifier,
            version=definition.version
        )

        # Record node identifier in requirement mapping to find out how many
        # nodes are required for the same definition identifier.
        self._required_definitions.setdefault(definition.identifier, set())
        self._required_definitions[definition.identifier].add(identifier)

        # Create the node if necessary
        if identifier not in self._nodes.keys():
            self._logger.debug("Adding definition: {}".format(identifier))

            self._nodes[identifier] = _GraphNode(
                identifier, definition, requirement, parent_identifier
            )

            for dependency_requirement in definition.get("dependency", []):
                self.update_from_requirement(
                    dependency_requirement,
                    parent_identifier=identifier
                )

        if parent_identifier is not None:
            self.add_link(identifier, parent_identifier)

    def add_link(self, identifier, parent_identifier):
        """Add dependency link from *parent_identifier* to *identifier*.

        *identifier* is the identifier of the node.

        *parent_identifier* is the identifier of a parent node.

        """
        self._logger.debug(
            "Add dependency link from {parent!r} to {child!r}".format(
                parent=parent_identifier, child=identifier
            )
        )

        self._links_from.setdefault(parent_identifier, [])
        self._links_from[parent_identifier].append(identifier)

        self._links_to.setdefault(identifier, [])
        self._links_to[identifier].append(parent_identifier)

    def prune_invalid_nodes(self):
        """Keep only the best matching definition versions required.

        Raise :exc:`RuntimeError` if two required versions are incompatible.

        """
        queue = Queue()

        # Record all node identifiers to preserve in the graph.
        valid_identifiers = []

        for node in self._nodes.values():
            if self.dependencies_number(node.identifier) == 0:
                queue.put(node)

        while not queue.empty():
            node = queue.get()

            # Get all node identifiers sharing a common definition identifier.
            identifiers = sorted(
                self._required_definitions[node.definition.identifier]
            )

            # Raise an error if the version is incompatible with other
            # node requirements.
            self._validate_node(node, identifiers)

            # Keep node if it is the best matching one
            if (
                node.identifier == identifiers[-1] and
                node.identifier not in valid_identifiers
            ):
                self._logger.debug("Keep '{}'".format(node.identifier))
                valid_identifiers.append(node.identifier)

                for parent_identifier in self.parents(node.identifier):
                    queue.put(self._nodes[parent_identifier])

        # Remove all nodes outside of the valid ones recorded
        for node in self._nodes.values():
            if node.identifier not in valid_identifiers:
                self._remove_node(node)

    def _validate_node(self, node, identifiers):
        """Validate *node* against equivalent node *identifiers*.

        *identifiers* must be nodes with the same definition identifier as
        *node*.

        Raise :exc:`RuntimeError` if two nodes are incompatible.

        """
        for identifier in identifiers:
            _node = self._nodes.get(identifier)

            if not self._compatible_nodes(node, _node):
                raise RuntimeError(
                    "A version conflict has been detected for '{id!r}'\n"
                    " - {node1}\n"
                    " - {node2}\n".format(
                        id=node.requirement,
                        node1=self._display_node(node),
                        node2=self._display_node(_node),
                    )
                )

    def _compatible_nodes(self, node1, node2):
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
        """Return formatted identifier for node instance."""
        message = "{}".format(node.requirement)

        if node.parent is not None:
            message += " [from {!r}]".format(node.parent.identifier)

        return message

    def _remove_node(self, node):
        """Remove *node* from graph."""
        # Remove node from nodes mapping.
        self._logger.debug("Remove {}".format(node.identifier))

        del self._nodes[node.identifier]

        # Remove node from required definition set.
        self._required_definitions[node.definition.identifier].remove(
            node.identifier
        )

        # Remove in-coming and out-coming links if necessary.
        if node.identifier in self._links_to.keys():
            del self._links_to[node.identifier]

        if node.identifier in self._links_from.keys():
            del self._links_from[node.identifier]

    def sorted_definitions(self):
        """Return topologically sorted list of definitions.

        Best matching :class:`~umwelt.definition.Definition` instances are
        extracted from each node instance and added to the list.

        Raise :exc:`RuntimeError` if the graph cannot be sorted.

        """
        queue = Queue()
        indegree_mapping = {}

        for node in self._nodes.values():
            indegree = self.dependencies_number(node.identifier)
            indegree_mapping[node.identifier] = indegree

            # Queue all node identifiers which have no dependencies
            if indegree_mapping[node.identifier] == 0:
                queue.put(node)

        definitions = []

        while not queue.empty():
            node = queue.get()

            # Ensure that no other nodes with the same definition identifier
            # is left in the tree.
            if len(self._required_definitions[node.definition.identifier]) > 1:
                raise RuntimeError(
                    "Several versions of the same definition identifier are "
                    "requested."
                )

            definitions.append(node.definition)

            for identifier in self.parents(node.identifier):
                indegree_mapping[identifier] = indegree_mapping[identifier] - 1

                if indegree_mapping[identifier] == 0:
                    queue.put(self._nodes[identifier])

        if len(definitions) != len(self._nodes):
            raise RuntimeError(
                "A cycle has been detected in the dependency graph"
            )

        self._logger.debug(
            "Topologically sorted definitions: {}".format(
                [definition.identifier for definition in definitions]
            )
        )

        return definitions

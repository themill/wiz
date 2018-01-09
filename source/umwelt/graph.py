# :coding: utf-8

import copy
from heapq import heapify, heappush, heappop
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import mlog

import umwelt.definition


class Graph(object):
    """Dependency Graph.

    A dependency graph can be created from required environment definitions.
    All possible definition versions will be created.

    """

    #: Identify the root of the graph
    ROOT = "root"

    def __init__(self, definition_mapping):
        """Initialise Graph.

        *definition_mapping* is a mapping regrouping all available environment
        definition associated with their unique identifier. It is used to
        resolve dependent definition specifiers.

        """
        self._logger = mlog.Logger(__name__ + ".Graph")

        # All available definitions.
        self._definitions = definition_mapping

        # All nodes created per node identifier.
        self._nodes = {}

        # Set of node identifiers organised per definition identifier.
        self._nodes_per_definition = {}

        # Record the weight of each link in the graph.
        self._links = dict()

    def node_identifiers(self):
        """Return all node identifiers in the graph."""
        return self._nodes.keys()

    def node_identifiers_from_definition(self, definition_identifier):
        """Return node identifiers in the graph from *definition_identifier*."""
        return filter(
            lambda _identifier: _identifier in self._nodes.keys(),
            self._nodes_per_definition[definition_identifier]
        )

    def node(self, identifier):
        """Return node from *identifier*."""
        return self._nodes.get(identifier)

    def indegree(self, identifier):
        """Return indegree number for node *identifier*."""
        return len(self.incoming(identifier))

    def outdegree(self, identifier):
        """Return outdegree number for node *identifier*."""
        return len(self.outcoming(identifier))

    def incoming(self, identifier):
        """Return incoming node identifiers for node *identifier*."""
        identifiers = []

        for node in self._nodes.keys():
            if identifier in self._links.get(node.identifier, {}).keys():
                identifiers.append(node.identifier)

        return identifiers

    def outcoming(self, identifier):
        """Return outcoming node identifiers for node *identifier*."""
        return filter(
            lambda _identifier: _identifier in self._nodes.keys(),
            self._links.get(identifier, {}).keys(),
        )

    def link_weight(self, identifier, parent_identifier):
        """Return weight from link between *parent_identifier* and *identifier*.
        """
        return self._links[parent_identifier][identifier].weight

    def link_requirement(self, identifier, parent_identifier):
        """Return requirement from link between *parent_identifier* and
        *identifier*.

        This should be a :class:`packaging.requirements.Requirement` instance.

        """
        return self._links[parent_identifier][identifier].requirement

    def conflicts(self):
        """Return conflicting node identifiers.

        A conflict appears when several nodes are found for a single
        definition.

        """
        identifiers = []

        for _identifiers in self._nodes_per_definition.values():
            if len(_identifiers) > 1:
                identifiers += _identifiers

        return identifiers

    def update_from_requirements(self, requirements, parent_identifier=None):
        """Recursively update graph from *requirements*.

        *requirements* should be a list of
        :class:`packaging.requirements.Requirement` instances ordered from the
        ost important to the least important.

        *parent_identifier* can indicate the identifier of a parent node.

        """
        # A weight is defined for each requirement based on the order. The
        # first node has a weight of 1 which indicates that it is the most
        # important node.
        weight = 1

        for requirement in requirements:
            self.update_from_requirement(
                requirement,
                parent_identifier=parent_identifier,
                weight=weight
            )

            weight += 1

    def update_from_requirement(
        self, requirement, parent_identifier=None, weight=1,
    ):
        """Recursively update graph from *requirement*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. The lesser this number, the higher is
        the importance of the link. Default is 1.

        *weight* is a number which indicate the importance the node.

        """
        self._logger.debug("Update from requirement: {}".format(requirement))

        # Create node in graph if necessary.
        node = self._create_node_branch(requirement)

        # Record node identifiers per definition to identify conflicts.
        self._nodes_per_definition.setdefault(node.definition.identifier, set())
        self._nodes_per_definition[node.definition.identifier].add(
            node.identifier
        )

        if parent_identifier is not None:
            node.add_parent(parent_identifier)

        # Create link with requirement and weight.
        self._create_link(
            node.identifier,
            parent_identifier or self.ROOT,
            requirement,
            weight=weight
        )

    def _create_node_branch(self, requirement):
        """Recursively create nodes from *requirement* if necessary.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        Return top-level node.

        """
        definition = umwelt.definition.get(requirement, self._definitions)
        node_identifier = _Node.generate_identifier(definition)

        # Add the node to the graph if necessary.
        if node_identifier not in self._nodes.keys():
            self._logger.debug("Adding definition: {}".format(node_identifier))
            self._nodes[node_identifier] = _Node(definition)

            requirements = definition.get("requirement")
            if requirements is not None:
                self.update_from_requirements(
                    requirements, parent_identifier=node_identifier
                )

        return self._nodes[node_identifier]

    def _create_link(
        self, identifier, parent_identifier, requirement, weight=1
    ):
        """Add dependency link from *parent_identifier* to *identifier*.

        *identifier* is the identifier of the environment which is added to the
        dependency graph.

        *parent_identifier* is the identifier of the targeted environment which
        must be linked to the new *identifier*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *weight* is a number which indicate the importance of the dependency
        link. The lesser this number, the higher is the importance of the link.
        Default is 1.

        Raise :exc:`RuntimeError` is *definition* identifier has already be
        set for this *parent*.

        """
        self._logger.debug(
            "Add dependency link from '{parent}' to '{child}'".format(
                parent=parent_identifier, child=identifier
            )
        )

        self._links.setdefault(parent_identifier, {})

        if identifier in self._links[parent_identifier].keys():
            raise RuntimeError(
                "There cannot be several dependency links to '{child}' from "
                "'{parent}'".format(
                    parent=parent_identifier, child=identifier
                )
            )

        link = _Link(requirement, weight=weight)
        self._links[parent_identifier][identifier] = link

    def remove_node(self, identifier):
        """Remove node from the graph.

        .. warning::

            A lazy deletion is performed as the links are not deleted to save on
            performance.

        """
        del self._nodes[identifier]


class _Node(object):
    """Node encapsulating a definition version in the graph.
    """

    def __init__(self, definition):
        """Initialise Node.

        *definition* indicates a :class:`~umwelt.definition.Definition`.

        """
        self._definition = definition
        self._parent_identifiers = set()

    @classmethod
    def generate_identifier(cls, definition):
        """Generate identifier from a :class:`~umwelt.definition.Definition`.
        """
        return "{definition}=={version}".format(
            definition=definition.identifier,
            version=definition.version
        )

    @property
    def identifier(self):
        """Return identifier of the node."""
        return self.generate_identifier(self._definition)

    @property
    def definition(self):
        """Return :class:`~umwelt.definition.Definition` encapsulated."""
        return self._definition

    @property
    def parent_identifiers(self):
        """Return set of parent identifiers."""
        return self._parent_identifiers

    def add_parent(self, identifier):
        """Add *identifier* as a parent to the node."""
        self._parent_identifiers.add(identifier)


class _Link(object):
    """Weighted link between two nodes in the graph.
    """

    def __init__(self, requirement, weight=1):
        """Initialise Link.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *weight* is a number which indicate the importance of the dependency
        link. default is 1. The lesser this number, the higher is the
        importance of the link.

        """
        self._requirement = requirement
        self._weight = weight

    @property
    def requirement(self):
        """Return requirement of the link.

        This should be a :class:`packaging.requirements.Requirement` instance.

        """
        return self._requirement

    @property
    def weight(self):
        """Return weight number of the link."""
        return self._weight


class _PriorityQueue(dict):
    """Priority mapping which can be used as a priority queue.

    Keys of the dictionary are node identifiers to be put into the queue, and
    values are their respective priorities. All dictionary methods work as
    expected.

    The advantage over a standard heapq-based priority queue is that priorities
    of node identifiers can be efficiently updated (amortized O(1)) using code
    as 'priority_stack[node] = new_priority.'

    .. note::

        Inspired by Matteo Dell'Amico's implementation:
        https://gist.github.com/matteodellamico/4451520

    """

    def __init__(self, *args, **kwargs):
        """Initialise mapping and build heap."""
        super(_PriorityQueue, self).__init__(*args, **kwargs)
        self._build_heap()

    def _build_heap(self):
        """Build the heap from mapping's keys and values."""
        self._heap = [
            (priority, identifier) for identifier, priority in self.items()
        ]
        heapify(self._heap)

    def __setitem__(self, identifier, priority):
        """Set *priority* value for *identifier* item.

        *identifier* should be a node identifier.

        *priority* should be a number indicating the importance of the node.

        .. note::

            The priority is not removed from the heap since this would have a
            cost of O(n).

        """
        super(_PriorityQueue, self).__setitem__(identifier, priority)

        if len(self._heap) < 2 * len(self):
            heappush(self._heap, (priority, identifier))
        else:
            # When the heap grows larger than 2 * len(self), we rebuild it
            # from scratch to avoid wasting too much memory.
            self._build_heap()

    def smallest(self):
        """Return the item with the lowest priority.

        Raises :exc:`IndexError` if the object is empty.

        """

        heap = self._heap
        priority, identifier = heap[0]

        while identifier not in self or self[identifier] != priority:
            heappop(heap)
            priority, identifier = heap[0]

        return identifier

    def pop_smallest(self):
        """Return the item with the lowest priority and remove it.

        Raises :exc:`IndexError` if the object is empty.

        """

        heap = self._heap
        priority, identifier = heappop(heap)

        while identifier not in self or self[identifier] != priority:
            priority, identifier = heappop(heap)

        del self[identifier]
        return identifier

    def yield_sorted_identifiers(self):
        """Generate list of node identifiers sorted by priority.

        .. warning::

            This will destroy elements as they are returned.

        """
        while self:
            yield self.pop_smallest()

    def empty(self):
        """Indicate whether the mapping is empty."""
        return len(self.keys()) == 0

    def setdefault(self, identifier, priority=None):
        """Set default *priority* value for *identifier* item.

        *identifier* should be a node identifier.

        *priority* should be a number indicating the importance of the node.

        .. note::

            This needs to be re-implemented to use the customized __setitem__
            method.

        """
        if identifier not in self:
            self[identifier] = priority
            return priority
        return self[identifier]

    def update(self, *args, **kwargs):
        """Update the mapping and rebuild the heap."""
        # Reimplementing dict.update is tricky -- see e.g.
        # http://mail.python.org/pipermail/python-ideas/2007-May/000744.html
        # We just rebuild the heap from scratch after passing to super.
        super(_PriorityQueue, self).update(*args, **kwargs)
        self._build_heap()


def resolve_conflicts(graph, definition_mapping):
    """Resolve all definition version conflicts in the graph if necessary.

    *graph* must be an instance of :class:`Graph`.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    Raise :exc:`RuntimeError` if two node requirements are incompatible.

    """
    logger = mlog.Logger(__name__ + ".resolve_conflicts")

    identifiers = graph.conflicts()
    if len(identifiers) == 0:
        logger.debug("No conflicts in the graph.")
        return

    while True:
        priority_mapping = compute_priority_mapping(graph)

        # Remove nodes unreachable from the root level.
        for identifier in graph.node_identifiers():
            if priority_mapping[identifier][0] is None:
                logger.debug("Remove '{}'".format(identifier))
                graph.remove_node(identifier)

        # If no identifiers are left in the queue, exit the loop.
        if len(identifiers) == 0:
            break

        # Sort identifiers per distance from the root level.
        identifiers = sorted(
            identifiers,
            key=lambda _identifier: priority_mapping[_identifier][0],
            reverse=True
        )

        # Pick up the nearest node.
        current_identifier = identifiers.pop()
        current_node = graph.node(current_identifier)

        # Identify other nodes conflicting with this node identifier.
        similar_identifiers = filter(
            lambda _identifier: _identifier != current_identifier,
            graph.node_identifiers_from_definition(
                current_node.definition.identifier
            )
        )

        # Ensure that all requirements from parent links are compatibles.
        validate_node_requirements(
            graph, current_identifier, similar_identifiers, priority_mapping
        )

        # Compute valid node identifier from combined requirements.
        requirement = combined_requirement(
            graph, [current_identifier] + similar_identifiers,
            priority_mapping
        )

        definition = umwelt.definition.get(requirement, definition_mapping)
        valid_identifier = _Node.generate_identifier(definition)

        if current_identifier != valid_identifier:
            logger.debug("Remove '{}'".format(current_identifier))
            graph.remove_node(current_identifier)

            # If the valid identifier is not in the graph, add it to the queue.
            if valid_identifier not in similar_identifiers:
                logger.debug(
                    "Append '{}' to conflicted nodes".format(valid_identifier)
                )
                identifiers.append(valid_identifier)
                graph.update_from_requirement(requirement)

        priority_mapping = compute_priority_mapping(graph)


def combined_requirement(graph, identifiers, priority_mapping):
    """Return combined requirement from node *identifiers* in *graph*.

    *graph* must be an instance of :class:`Graph`.

    *identifiers* must be valid node identifiers.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    Raise :exc:`RuntimeError` if requirements cannot be combined.

    """
    requirement = None

    for identifier in identifiers:
        _requirement = graph.link_requirement(
            identifier, priority_mapping[identifier][1]
        )

        if requirement is None:
            requirement = copy.copy(_requirement)

        elif requirement.name != _requirement.name:
            raise RuntimeError(
                "Impossible to combine requirements with different names "
                "['{}' and '{}'].".format(requirement.name, _requirement.name)
            )

        else:
            requirement.specifier &= _requirement.specifier

    return requirement


def validate_node_requirements(
    graph, identifier, identifiers, priority_mapping
):
    """Validate node *identifier* against other node *identifiers* in *graph*.

    *graph* must be an instance of :class:`Graph`.

    *identifier* and *identifiers* must be valid node identifiers.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    Raise :exc:`RuntimeError` if two node requirements are incompatible.

    """
    for _identifier in identifiers:
        if not compatible_in_graph(
            graph, identifier, _identifier, priority_mapping
        ):
            node = graph.node(identifier)

            raise RuntimeError(
                "A requirement conflict has been detected for '{definition}'\n"
                " - {requirement1} [from {parent1}]\n"
                " - {requirement2} [from {parent2}]\n".format(
                    definition=node.definition.identifier,
                    requirement1=graph.link_requirement(
                        identifier, priority_mapping[identifier][1]
                    ),
                    requirement2=graph.link_requirement(
                        _identifier, priority_mapping[_identifier][1]
                    ),
                    parent1=priority_mapping[identifier][1],
                    parent2=priority_mapping[_identifier][1],
                )
            )


def compatible_in_graph(graph, identifier1, identifier2, priority_mapping):
    """Check node *identifier1* compatibility against node *identifiers2*.

    Ensure that both node requirements are compatible within the *graph*.

    *graph* must be an instance of :class:`Graph`.

    *identifier1* and *identifier2* must be valid node identifiers.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    Raise :exc:`RuntimeError` if two nodes are incompatible.

    """
    logger = mlog.Logger(__name__ + ".validate_node_requirements")

    node1 = graph.node(identifier1)
    requirement1 = graph.link_requirement(
        identifier1, priority_mapping[identifier1][1]
    )

    node2 = graph.node(identifier2)
    requirement2 = graph.link_requirement(
        identifier2, priority_mapping[identifier2][1]
    )

    # Nodes are not compatible if both definition versions are not
    # compatible with at least one of the specifier.
    if (
        node1.definition.version not in requirement2.specifier and
        node2.definition.version not in requirement1.specifier
    ):
        return False

    # Nodes are not compatible if different variants were requested.
    if requirement1.extras != requirement2.extras:
        return False

    logger.debug(
        "'{requirement1}' and '{requirement2}' are compatibles".format(
            requirement1=requirement1,
            requirement2=requirement2
        )
    )

    return True


def compute_priority_mapping(graph):
    """Return priority mapping for each node of *graph*.

    The mapping indicates the lowest possible priority of each node identifier
    from the root level of the graph with its corresponding parent node
    identifier.

    The priority is defined by the sum of the weights from each node to the
    root level.

    *graph* must be an instance of :class:`Graph`.

    This is using `Dijkstra's shortest path algorithm
    <https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm>`_.

    .. note::

        When a node is being visited twice, the path with the smallest priority
        is being kept.

    """
    logger = mlog.Logger(__name__ + ".compute_priority_mapping")

    # Initiate mapping
    priority_mapping = {
        node_identifier: (None, None) for node_identifier
        in graph.node_identifiers()
    }

    priority_mapping[graph.ROOT] = (0, graph.ROOT)

    queue = _PriorityQueue()
    queue[graph.ROOT] = 0

    while not queue.empty():
        identifier = queue.pop_smallest()
        current_priority = priority_mapping[identifier][0]

        for child_identifier in graph.outcoming(identifier):
            priority = current_priority + graph.link_weight(
                child_identifier, identifier
            )

            # The last recorded priority of this node from the source
            last_priority = priority_mapping[child_identifier][0]

            # If there is a currently recorded priority from the source and this
            # is lesser than the priority of the node found, update the current
            # priority from the root level in the mapping.
            if last_priority is None or last_priority < priority:
                priority_mapping[child_identifier] = (priority, identifier)
                queue[child_identifier] = priority

                logger.debug(
                    "Priority {priority} set to '{node}' from '{parent}'"
                    .format(
                        priority=priority,
                        node=child_identifier,
                        parent=identifier
                    )
                )

    return priority_mapping


def extract_ordered_definitions(graph):
    """Return topologically sorted list of definitions from *graph*.

    Best matching :class:`~umwelt.definition.Definition` instances are
    extracted from each node instance and added to the list.

    Raise :exc:`RuntimeError` if the graph cannot be sorted.

    """
    logger = mlog.Logger(__name__ + ".extract_ordered_definitions")

    queue = Queue()
    outdegree_mapping = {}

    for identifier in graph.node_identifiers():
        outdegree = graph.outdegree(identifier)
        outdegree_mapping[identifier] = outdegree

        # Queue all node identifiers which have no dependencies.
        if outdegree_mapping[identifier] == 0:
            queue.put(graph.node(identifier))

    definitions = []

    while not queue.empty():
        node = queue.get()
        definitions.append(node.definition)

        for identifier in node.parent_identifiers:
            if identifier not in outdegree_mapping.keys():
                continue

            outdegree_mapping[identifier] = (
                outdegree_mapping[identifier] - 1
            )

            if outdegree_mapping[identifier] == 0:
                queue.put(graph.node(identifier))

    if len(definitions) != len(graph.node_identifiers()):
        raise RuntimeError(
            "A cycle has been detected in the dependency graph"
        )

    logger.debug(
        "Topologically sorted definitions: {}".format(
            [definition.identifier for definition in definitions]
        )
    )

    return definitions

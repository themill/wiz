# :coding: utf-8

import copy
import hashlib
import itertools
from collections import deque
from collections import namedtuple
from heapq import heapify, heappush, heappop
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import mlog

import wiz.environment
import wiz.exception


#: Weighted link associating nodes in the requirement graph.
_Link = namedtuple("_Link", "requirement, weight")

#: Element with palatable properties access used to create the priority mapping.
_NodeAttributes = namedtuple("_NodeAttributes", "priority, parent")


class Resolver(object):
    """Graph resolver class."""

    def __init__(self, environment_mapping):
        """Initialise Resolver with *requirements*.

        *environment_mapping* is a mapping regrouping all available environments
        associated with their unique identifier.

        """
        self._logger = mlog.Logger(__name__ + ".Resolver")

        # All available environments.
        self._environment_mapping = environment_mapping

        # Stack of all graphs to resolve, sorted from the least important to
        # the most important.
        self._graphs_stack = deque()

    @property
    def graphs(self):
        """Return the number of requirement graphs added to the stack."""
        return len(self._graphs_stack)

    @property
    def environment_mapping(self):
        """Return mapping of all available environments."""
        return self._environment_mapping

    def compute_environments(self, requirements):
        """Resolve requirements graphs and return list of environment versions.

        *requirements* should be a list of
        class:`packaging.requirements.Requirement` instances.

        """
        graph = Graph(self)
        graph.update_from_requirements(requirements)

        # Initialise stack.
        self._graphs_stack = deque([graph])

        while len(self._graphs_stack) != 0:
            graph = self._graphs_stack.pop()

            priority_mapping = self.compute_priority_mapping(graph)

            # Check if the graph must be divided.
            if self.divide(graph, priority_mapping) > 0:
                continue

            try:
                self.resolve_conflicts(graph)

            except wiz.exception.WizError as error:
                # If no more graphs is left to resolve, raise an error.
                if len(self._graphs_stack) == 0:
                    raise
                self._logger.debug("Failed to resolve graph: {}".format(error))

            else:
                priority_mapping = self.compute_priority_mapping(graph)
                return self.extract_ordered_environments(
                    graph, priority_mapping
                )

    def divide(self, graph, priority_mapping):
        """Divide *graph* if necessary and return number of graphs created.

        A *graph* must be divided when it contains at least one environment
        version node with more than one variant available. The total number
        of graphs created will be equal to the multiplication of each variant
        number.

        The nearest nodes are computed first, and the order of variants within
        each environment version is preserved so that the graphs created are
        added to the stack from the most important to the least important.

        *graph* must be an instance of :class:`Graph`.

        *priority_mapping* is a mapping indicating the lowest possible priority
        of each node identifier from the root level of the graph with its
        corresponding parent node identifier.

        """
        variant_groups = graph.variant_groups()
        if len(variant_groups) == 0:
            self._logger.debug("No alternative graphs created.")
            return 0

        # Order the variant groups per priority to compute those nearest to the
        # top-level first. Each node from a variant group should have the same
        # priority, so we can sort the group list by using the first identifier
        # of each group as a key reference.
        sorted_variant_groups = sorted(
            variant_groups,
            key=lambda _group: priority_mapping[_group[0]].priority,
        )

        graph_list = [graph.copy()]

        for variant_group in sorted_variant_groups:
            new_graph_list = []

            # For each graph in the list, create an alternative graph with each
            # isolated node identifier from the variant group.
            for _graph in graph_list:
                for node_identifier in variant_group:
                    copied_graph = _graph.copy()
                    other_identifiers = (
                        _id for _id in variant_group if _id != node_identifier
                    )

                    # Remove all other variant from the variant graph.
                    for _identifier in other_identifiers:
                        copied_graph.remove_node(_identifier)

                    new_graph_list.append(copied_graph)

            # Re-initiate the graph list with the new graph divisions.
            graph_list = new_graph_list

        # Add new graph to the stack.
        for _graph in reversed(graph_list):
            _graph.reset_variant_groups()
            self._graphs_stack.append(_graph)

        number = len(graph_list)
        self._logger.debug("graph divided into {} new graphs.".format(number))
        return number

    def resolve_conflicts(self, graph):
        """Attempt to resolve all conflicts in *graph*.

        *graph* must be an instance of :class:`Graph`.

        Raise :exc:`wiz.exception.GraphResolutionError` if two node requirements
        are incompatible.

        Raise :exc:`wiz.exception.GraphResolutionError` if new environment
        versions added to the graph during the resolution process lead to
        a division of the graph.

        """
        identifiers = graph.conflicts()
        if len(identifiers) == 0:
            self._logger.debug("No conflicts in the graph.")
            return

        self._logger.debug("Conflicts: {}".format(", ".join(identifiers)))

        while True:
            priority_mapping = self.compute_priority_mapping(graph)

            # Update graph and conflict identifiers list to remove all
            # unreachable nodes.
            self._remove_unreachable_nodes(graph, priority_mapping)
            identifiers = filter(
                lambda _id: priority_mapping.get(_id), identifiers
            )

            # If no identifiers are left in the queue, exit the loop. The graph
            # is officially resolved. Hooray.
            if len(identifiers) == 0:
                return

            # Sort identifiers per distance from the root level.
            identifiers = sorted(
                identifiers, key=lambda _id: priority_mapping[_id].priority,
            )

            # Pick up the nearest node.
            identifier = identifiers.pop()

            # Identify other nodes conflicting with this node identifier.
            conflicted_identifiers = self.conflicted_identifiers(
                graph, identifier
            )

            # Ensure that all requirements from parent links are compatibles.
            self.validate_node_requirements(
                graph, identifier, conflicted_identifiers
            )

            # Compute valid node identifier from combined requirements.
            requirement = self.combined_requirement(
                graph, [identifier] + conflicted_identifiers, priority_mapping
            )

            # Query identifiers from combined requirement.
            _identifiers = self.identifiers_from_requirement(requirement)

            if identifier not in _identifiers:
                self._logger.debug("Remove '{}'".format(identifier))
                graph.remove_node(identifier)

                # If some of the newly queried identifiers are not in the list
                # of conflicted nodes, that means that the requirement should
                # be added to the graph.
                new_identifiers = set(_identifiers).difference(
                    set(conflicted_identifiers)
                )

                if len(new_identifiers) > 0:
                    self._logger.debug(
                        "Add to graph: ".format(", ".join(new_identifiers))
                    )
                    graph.update_from_requirement(requirement)

                    # Update conflict list if necessary.
                    identifiers = list(set(identifiers + graph.conflicts()))

                    # Check if the graph must be divided. If this is the case,
                    # the current graph cannot be resolved.
                    priority_mapping = self.compute_priority_mapping(graph)
                    if self.divide(graph, priority_mapping) > 0:
                        raise wiz.exception.GraphResolutionError(
                            "The current graph has been divided."
                        )

    def conflicted_identifiers(self, graph, identifier):
        """Return identifiers from nodes conflicting with node *identifier*.

        A node from the *graph* is in conflict with the node *identifier* when
        its environment identifier is identical.

        *graph* must be an instance of :class:`Graph`.

        *identifiers* must be valid node identifiers.

        """
        node = graph.node(identifier)

        # Extract environment identifier from node.
        environment = node.environment.identifier

        # Get all nodes in the graph with the same environment identifier.
        identifiers = graph.node_identifiers_from_environment(environment)

        return filter(lambda _id: _id != identifier, identifiers)

    def identifiers_from_requirement(self, requirement):
        """Return list of nodes identifiers requested from *requirement*

        .. note::

            The nodes will **NOT** be created in any graphs.

        """
        environments = wiz.environment.get(
            requirement, self.environment_mapping
        )
        return map(_Node.generate_identifier, environments)

    def _remove_unreachable_nodes(self, graph, priority_mapping):
        """Remove unreachable nodes from *graph* based on *priority_mapping*.

        If a node within the *graph* does not have a priority, it means that it
        cannot be reached from the root level. It will then be lazily removed
        from the graph (the links are preserved to save on computing time).

        *graph* must be an instance of :class:`Graph`.

        *priority_mapping* is a mapping indicating the lowest possible priority
        of each node identifier from the root level of the graph with its
        corresponding parent node identifier.

        """
        for identifier in graph.node_identifiers():
            if priority_mapping[identifier].priority is None:
                self._logger.debug("Remove '{}'".format(identifier))
                graph.remove_node(identifier)

    def validate_node_requirements(self, graph, identifier, identifiers):
        """Validate node *identifier* against other *identifiers* in *graph*.

        *graph* must be an instance of :class:`Graph`.

        *identifier* and *identifiers* must be valid node identifiers.

        Raise :exc:`wiz.exception.GraphResolutionError` if two node requirements
        are incompatible.

        """
        node1 = graph.node(identifier)
        mapping1 = self.compute_requirement_mapping(graph, identifier)

        for identifier2 in identifiers:
            node2 = graph.node(identifier2)
            mapping2 = self.compute_requirement_mapping(graph, identifier2)

            for requirement1, requirement2 in itertools.combinations(
                mapping1.keys() + mapping2.keys(), 2
            ):
                conflict = False

                # Nodes are not compatible if both environment versions are not
                # compatible with at least one of the specifier.
                if (
                    node1.environment.version not in requirement2.specifier and
                    node2.environment.version not in requirement1.specifier
                ):
                    conflict = True

                # Nodes are not compatible if different variants were requested.
                elif requirement1.extras != requirement2.extras:
                    conflict = True

                if conflict:
                    raise wiz.exception.GraphResolutionError(
                        "A requirement conflict has been detected for "
                        "'{environment}'\n"
                        " - {requirement1} [from {parent1}]\n"
                        " - {requirement2} [from {parent2}]\n".format(
                            environment=node1.environment.identifier,
                            requirement1=requirement1,
                            requirement2=requirement2,
                            parent1=mapping1[requirement1],
                            parent2=mapping2[requirement2],
                        )
                    )

                self._logger.debug(
                    "'{requirement1}' and '{requirement2}' are "
                    "compatibles".format(
                        requirement1=requirement1,
                        requirement2=requirement2
                    )
                )

    def combined_requirement(self, graph, identifiers, priority_mapping):
        """Return combined requirement from node *identifiers* in *graph*.

        *graph* must be an instance of :class:`Graph`.

        *identifiers* must be valid node identifiers.

        *priority_mapping* is a mapping indicating the lowest possible priority
        of each node identifier from the root level of the graph with its
        corresponding parent node identifier.

        Raise :exc:`wiz.exception.GraphResolutionError` if requirements cannot
        be combined.

        """
        requirement = None

        for identifier in identifiers:
            _requirement = graph.link_requirement(
                identifier, priority_mapping[identifier].parent
            )

            if requirement is None:
                requirement = copy.copy(_requirement)

            elif requirement.name != _requirement.name:
                raise wiz.exception.GraphResolutionError(
                    "Impossible to combine requirements with different names "
                    "['{}' and '{}'].".format(
                        requirement.name, _requirement.name
                    )
                )

            else:
                requirement.specifier &= _requirement.specifier

        return requirement

    def compute_requirement_mapping(self, graph, identifier):
        """Return mapping regrouping all requirements for node *identifier*.

        The mapping associates each requirement name with a parent *identifier*.

        *graph* must be an instance of :class:`Graph`.

        *identifier* and *identifiers* must be valid node identifiers.

        """
        node = graph.node(identifier)

        # Filter out non existing nodes from incoming.
        incoming_identifiers = filter(
            lambda _id: graph.node(_id) is not None or _id == Graph.ROOT,
            node.parent_identifiers
        )

        mapping = {}

        for incoming_identifier in incoming_identifiers:
            requirement = graph.link_requirement(
                identifier, incoming_identifier
            )
            mapping[requirement] = incoming_identifier

        return mapping

    def extract_ordered_environments(self, graph, priority_mapping):
        """Return sorted list of environments from *graph*.

        Best matching :class:`~wiz.environment.Environment` instances are
        extracted from each node instance and added to the list.

        *priority_mapping* is a mapping indicating the lowest possible priority
        of each node identifier from the root level of the graph with its
        corresponding parent node identifier.

        """
        environments = []

        for identifier in sorted(
            graph.node_identifiers(),
            key=lambda _identifier: priority_mapping[_identifier],
            reverse=True
        ):
            node = graph.node(identifier)
            environments.append(node.environment)

        self._logger.debug(
            "Sorted environments: {}".format(
                ", ".join([
                    _Node.generate_identifier(_env) for _env in environments
                ])
            )
        )
        return environments

    def compute_priority_mapping(self, graph):
        """Return priority mapping for each node of *graph*.

        The mapping indicates the lowest possible priority of each node
        identifier from the root level of the graph with its corresponding
        parent node identifier.

        The priority is defined by the sum of the weights from each node to the
        root level.

        *graph* must be an instance of :class:`Graph`.

        This is using `Dijkstra's shortest path algorithm
        <https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm>`_.

        .. note::

            When a node is being visited twice, the path with the smallest
            priority is being kept.

        """
        self._logger.debug("Compute priority mapping...")

        # Initiate mapping
        priority_mapping = {
            node_identifier: _NodeAttributes(None, None) for node_identifier
            in graph.node_identifiers()
        }

        priority_mapping[graph.ROOT] = _NodeAttributes(0, graph.ROOT)

        queue = _PriorityQueue()
        queue[graph.ROOT] = 0

        while not queue.empty():
            identifier = queue.pop_smallest()
            current_priority = priority_mapping[identifier].priority

            for child_identifier in graph.outcoming(identifier):
                priority = current_priority + graph.link_weight(
                    child_identifier, identifier
                )

                # The last recorded priority of this node from the source
                last_priority = priority_mapping[child_identifier].priority

                # If there is a currently recorded priority from the source and
                # this is lesser than the priority of the node found, update the
                # current priority from the root level in the mapping.
                if last_priority is None or last_priority < priority:
                    priority_mapping[child_identifier] = _NodeAttributes(
                        priority, identifier
                    )
                    queue[child_identifier] = priority

                    self._logger.debug(
                        "Priority {priority} set to '{node}' from '{parent}'"
                        .format(
                            priority=priority,
                            node=child_identifier,
                            parent=identifier
                        )
                    )

        return priority_mapping


class Graph(object):
    """Requirement Graph."""

    #: Identify the root of the graph
    ROOT = "root"

    def __init__(
        self, resolver, node_mapping=None, environment_mapping=None,
        variant_mapping=None, link_mapping=None
    ):
        """Initialise Graph.

        *resolver* should be an instance of :class:`Resolver`.

        *node_mapping* can be an initial mapping of nodes organised node
        identifier.

        *environment_mapping* can be an initial mapping of node identifier sets
        organised per environment identifier.

        *variant_mapping* can be an initial mapping of node identifier variant
        lists organised per unique variant group identifier.

        *link_mapping* can be an initial mapping of node identifiers
        association.

        """
        self._logger = mlog.Logger(__name__ + ".Graph")
        self._resolver = resolver

        # All nodes created per node identifier.
        self._node_mapping = node_mapping or {}

        # Set of node identifiers organised per environment identifier.
        self._environment_mapping = environment_mapping or {}

        # List of node identifier variants per hashed variant group identifier.
        self._variant_mapping = variant_mapping or {}

        # Record the weight of each link in the graph.
        self._link_mapping = link_mapping or {}

    def copy(self):
        """Return a copy of the graph."""
        return Graph(
            self._resolver,
            node_mapping=self._node_mapping.copy(),
            environment_mapping=self._environment_mapping.copy(),
            variant_mapping=self._variant_mapping.copy(),
            link_mapping=self._link_mapping.copy()
        )

    def node_identifiers(self):
        """Return all node identifiers in the graph."""
        return self._node_mapping.keys()

    def _node_exists(self, identifier):
        """Indicate whether the node *identifier* is in the graph."""
        return identifier in self._node_mapping.keys()

    def node_identifiers_from_environment(self, environment_identifier):
        """Return node identifiers in the graph from *environment_identifier*.
        """
        return filter(
            lambda _identifier: self._node_exists(_identifier),
            self._environment_mapping[environment_identifier]
        )

    def variant_groups(self):
        """Return list of variant node identifier groups."""
        return self._variant_mapping.values()

    def node(self, identifier):
        """Return node from *identifier*."""
        return self._node_mapping.get(identifier)

    def outdegree(self, identifier):
        """Return outdegree number for node *identifier*."""
        return len(self.outcoming(identifier))

    def outcoming(self, identifier):
        """Return outcoming node identifiers for node *identifier*."""
        return filter(
            lambda _identifier: self._node_exists(_identifier),
            self._link_mapping.get(identifier, {}).keys(),
        )

    def link_weight(self, identifier, parent_identifier):
        """Return weight from link between *parent_identifier* and *identifier*.
        """
        return self._link_mapping[parent_identifier][identifier].weight

    def link_requirement(self, identifier, parent_identifier):
        """Return requirement from link between *parent_identifier* and
        *identifier*.

        This should be a :class:`packaging.requirements.Requirement` instance.

        """
        return self._link_mapping[parent_identifier][identifier].requirement

    def conflicts(self):
        """Return conflicting node identifiers.

        A conflict appears when several nodes are found for a single
        environment.

        """
        identifiers = []

        for _identifiers in self._environment_mapping.values():
            if len(_identifiers) > 1:
                identifiers += filter(
                    lambda _identifier: self._node_exists(_identifier),
                    _identifiers,
                )

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

        # Get best matching environments from requirement.
        environments = wiz.environment.get(
            requirement, self._resolver.environment_mapping
        )
        identifiers = map(_Node.generate_identifier, environments)

        # If more than one environments is returned, record all node identifiers
        # into a variant group.
        if len(environments) > 1:
            hashed_object = hashlib.md5("".join(identifiers))
            self._variant_mapping[hashed_object.hexdigest()] = identifiers

        # Create a node for each environment version if necessary.
        for environment, identifier in itertools.izip(
            environments, identifiers
        ):
            if identifier not in self._node_mapping.keys():
                self._logger.debug("Adding environment: {}".format(identifier))
                self._node_mapping[identifier] = _Node(environment)

                requirements = environment.get("requirement")
                if requirements is not None:
                    self.update_from_requirements(
                        requirements, parent_identifier=identifier
                    )

            node = self._node_mapping[identifier]

            # Record node identifiers per environment to identify conflicts.
            self._environment_mapping.setdefault(environment.identifier, set())
            self._environment_mapping[environment.identifier].add(
                node.identifier
            )

            node.add_parent(parent_identifier or self.ROOT)

            # Create link with requirement and weight.
            self._create_link(
                node.identifier,
                parent_identifier or self.ROOT,
                requirement,
                weight=weight
            )

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

        Raise :exc:`wiz.exception.IncorrectEnvironment` is *environment*
        identifier has already be set for this *parent*.

        """
        self._logger.debug(
            "Add dependency link from '{parent}' to '{child}'".format(
                parent=parent_identifier, child=identifier
            )
        )

        self._link_mapping.setdefault(parent_identifier, {})

        if identifier in self._link_mapping[parent_identifier].keys():
            raise wiz.exception.IncorrectEnvironment(
                "There cannot be several dependency links to '{child}' from "
                "'{parent}'.".format(parent=parent_identifier, child=identifier)
            )

        link = _Link(requirement, weight)
        self._link_mapping[parent_identifier][identifier] = link

    def remove_node(self, identifier):
        """Remove node from the graph.

        .. warning::

            A lazy deletion is performed as the links are not deleted to save on
            performance.

        """
        del self._node_mapping[identifier]

    def reset_variant_groups(self):
        """Reset list of variant node identifier groups .

        .. warning::

            A lazy deletion is performed as only the variant identifiers are
            deleted, but not the nodes themselves.

        """
        self._variant_mapping = {}


class _Node(object):
    """Node encapsulating a environment version in the graph.
    """

    def __init__(self, environment):
        """Initialise Node.

        *environment* indicates a :class:`~wiz.environment.Environment`.

        """
        self._environment = environment
        self._parent_identifiers = set()

    @classmethod
    def generate_identifier(cls, environment):
        """Generate identifier from an *environment*.

        *environment* indicates a :class:`~wiz.environment.Environment`.

        """
        variant_name = environment.get("variant_name")
        if variant_name is not None:
            variant_name = "[{}]".format(variant_name)

        return "{environment}{variant}=={version}".format(
            environment=environment.identifier,
            version=environment.version,
            variant=variant_name or ""
        )

    @property
    def identifier(self):
        """Return identifier of the node."""
        return self.generate_identifier(self._environment)

    @property
    def environment(self):
        """Return :class:`~wiz.environment.Environment` encapsulated."""
        return self._environment

    @property
    def parent_identifiers(self):
        """Return set of parent identifiers."""
        return self._parent_identifiers

    def add_parent(self, identifier):
        """Add *identifier* as a parent to the node."""
        self._parent_identifiers.add(identifier)


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

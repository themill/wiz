# :coding: utf-8

import copy
import uuid
from collections import deque
from heapq import heapify, heappush, heappop
try:
    import queue as _queue
except ImportError:
    import Queue as _queue

import mlog

import wiz.package
import wiz.exception
import wiz.symbol
import wiz.history


class Resolver(object):
    """Graph resolver class."""

    def __init__(self, definition_mapping):
        """Initialise Resolver with *requirements*.

        *definition_mapping* is a mapping regrouping all available definitions
        associated with their unique identifier.

        """
        self._logger = mlog.Logger(__name__ + ".Resolver")

        # All available definitions.
        self._definition_mapping = definition_mapping

        # List of definition identifiers with variants which required graph
        # division
        self._definitions_with_variants = []

        # Stack of all graphs to resolve, sorted from the least important to
        # the most important.
        self._graphs_stack = deque()

    @property
    def definition_mapping(self):
        """Return mapping of all available definitions."""
        return self._definition_mapping

    def compute_packages(self, requirements):
        """Resolve requirements graphs and return list of packages.

        *requirements* should be a list of
        class:`packaging.requirements.Requirement` instances.

        """
        graph = Graph(self)

        # Record the graph creation to the history if necessary.
        wiz.history.record_action(wiz.symbol.GRAPH_CREATION_ACTION, graph=graph)

        # Update the graph.
        graph.update_from_requirements(requirements)

        # Initialise stack.
        self._graphs_stack = deque([graph])

        while len(self._graphs_stack) != 0:
            graph = self._graphs_stack.pop()

            priority_mapping = compute_priority_mapping(graph)

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
                priority_mapping = compute_priority_mapping(graph)
                return extract_ordered_packages(graph, priority_mapping)

    def divide(self, graph, priority_mapping):
        """Divide *graph* if necessary and return number of graphs created.

        A *graph* must be divided when it contains at least one definition
        version with more than one variant. The total number of graphs created
        will be equal to the multiplication of each variant number.

        The nearest nodes are computed first, and the order of variants within
        each package version is preserved so that the graphs created are
        added to the stack from the most important to the least important.

        *graph* must be an instance of :class:`Graph`.

        *priority_mapping* is a mapping indicating the lowest possible priority
        of each node identifier from the root level of the graph with its
        corresponding parent node identifier.

        """
        variant_mapping = graph.variant_mapping()
        if len(variant_mapping) == 0:
            self._logger.debug("No alternative graphs created.")
            return 0

        # Record all definition identifiers which led to graph division.
        self._definitions_with_variants.extend(variant_mapping.keys())

        # Order the variant groups per priority to compute those nearest to the
        # top-level first. We can assume that the first identifier of each group
        # is the node with the highest priority as the graph has been updated
        # using a Breadth First Search algorithm.
        variant_groups = sorted(
            variant_mapping.values(),
            key=lambda _group: priority_mapping[_group[0]].get("priority"),
        )

        graph_list = [graph.copy()]

        for variant_group in variant_groups:
            mapping = {}
            variant_names = []

            # Regroup corresponding nodes per variant to prevent treating
            # conflicts as variants.
            for node_identifier in variant_group:
                node = graph.node(node_identifier)
                mapping.setdefault(node.variant_name, [])
                mapping[node.variant_name].append(node_identifier)

                # Record variant in list to preserve order
                if node.variant_name not in variant_names:
                    variant_names.append(node.variant_name)

            new_graph_list = []

            # For each graph in list, create an alternative graph containing
            # only node with common variant from this group
            for _graph in graph_list:
                for variant_name in variant_names:
                    identifiers = mapping[variant_name]
                    copied_graph = _graph.copy()
                    other_identifiers = (
                        node_identifier for node_identifier in variant_group
                        if node_identifier not in identifiers
                    )

                    # Remove all other variant from the variant graph.
                    for _identifier in other_identifiers:
                        copied_graph.remove_node(_identifier, record=False)

                    new_graph_list.append(copied_graph)

            # Re-initiate the graph list with the new graph divisions.
            graph_list = new_graph_list

        # Add new graph to the stack.
        for _graph in reversed(graph_list):
            _graph.reset_variants()
            self._graphs_stack.append(_graph)

            # Record the graph creation to the history if necessary.
            wiz.history.record_action(
                wiz.symbol.GRAPH_DIVISION_ACTION, origin=graph, graph=_graph
            )

        number = len(graph_list)
        self._logger.debug("graph divided into {} new graphs.".format(number))
        return number

    def resolve_conflicts(self, graph):
        """Attempt to resolve all conflicts in *graph*.

        *graph* must be an instance of :class:`Graph`.

        Raise :exc:`wiz.exception.GraphResolutionError` if two node requirements
        are incompatible.

        Raise :exc:`wiz.exception.GraphResolutionError` if new package
        versions added to the graph during the resolution process lead to
        a division of the graph.

        """
        conflicts = graph.conflicts()
        if len(conflicts) == 0:
            self._logger.debug("No conflicts in the graph.")
            return

        self._logger.debug("Conflicts: {}".format(", ".join(conflicts)))

        wiz.history.record_action(
            wiz.symbol.GRAPH_CONFLICTS_IDENTIFICATION_ACTION,
            graph=graph, conflicted_nodes=conflicts
        )

        while True:
            priority_mapping = compute_priority_mapping(graph)

            # Update graph and conflicts to remove all unreachable nodes.
            trim_unreachable_from_graph(graph, priority_mapping)
            conflicts = sorted_from_priority(conflicts, priority_mapping)

            # If no nodes are left in the queue, exit the loop. The graph
            # is officially resolved. Hooray!
            if len(conflicts) == 0:
                return

            # Pick up the nearest conflicted node identifier.
            identifier = conflicts.pop()
            node = graph.node(identifier)

            # Identify nodes conflicting with this node.
            conflicted_nodes = extract_conflicted_nodes(graph, node)

            # Compute valid node identifier from combined requirements.
            requirement = combined_requirements(
                graph, [node] + conflicted_nodes, priority_mapping
            )

            # Query packages from combined requirement.
            try:
                packages = wiz.package.extract(
                    requirement, self._definition_mapping
                )
            except wiz.exception.RequestNotFound:
                _parents = extract_parents(graph, [node] + conflicted_nodes)

                # Discard conflicted node if parents are themselves conflicting.
                if len(_parents.intersection(conflicts)) > 0:
                    continue

                raise wiz.exception.GraphResolutionError(
                    "The combined requirement '{}' could not be resolved from "
                    "the following packages: {!r}.\n".format(
                        requirement, sorted(_parents)
                    )
                )

            identifiers = [package.identifier for package in packages]

            if identifier not in identifiers:
                self._logger.debug("Remove '{}'".format(identifier))
                remove_node_and_relink(graph, node, identifiers, requirement)

                # Identify whether some of the newly extracted packages are not
                # in the list of conflicted nodes to decide if the graph should
                # be updated.
                _identifiers = set(identifiers).difference(
                    set([_node.identifier for _node in conflicted_nodes])
                )

                # If not all extracted packages are identified as conflicts, it
                # means that variants need to be added to the  graph. If
                # variants from this definition identifier have  already been
                # processed, the update is skipped.
                if (
                    len(_identifiers) == len(conflicted_nodes) and
                    node.definition not in self._definitions_with_variants
                ):
                    self._logger.debug(
                        "Add to graph: {}".format(", ".join(_identifiers))
                    )
                    graph.update_from_requirements([requirement])

                    # Update conflict list if necessary.
                    conflicts = list(set(conflicts + graph.conflicts()))

                    # Check if the graph must be divided. If this is the case,
                    # the current graph cannot be resolved.
                    priority_mapping = compute_priority_mapping(graph)

                    if self.divide(graph, priority_mapping) > 0:
                        raise wiz.exception.GraphResolutionError(
                            "The current graph has been divided."
                        )


def compute_priority_mapping(graph):
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
    logger = mlog.Logger(__name__ + ".compute_priority_mapping")
    logger.debug("Compute priority mapping...")

    # Initiate mapping
    priority_mapping = {
        node.identifier: {"priority": None, "parent": None}
        for node in graph.nodes()
    }

    priority_mapping[graph.ROOT] = {"priority": 0, "parent": graph.ROOT}

    queue = _PriorityQueue()
    queue[graph.ROOT] = 0

    while not queue.empty():
        identifier = queue.pop_smallest()
        current_priority = priority_mapping[identifier]["priority"]

        for child_identifier in graph.outcoming(identifier):
            priority = current_priority + graph.link_weight(
                child_identifier, identifier
            )

            # The last recorded priority of this node from the source
            last_priority = priority_mapping[child_identifier]["priority"]

            # If there is a currently recorded priority from the source and
            # this is superior than the priority of the node found, update
            # the current priority with the new one.
            if last_priority is None or last_priority > priority:
                priority_mapping[child_identifier] = {
                    "priority": priority, "parent": identifier
                }
                queue[child_identifier] = priority

                logger.debug(
                    "Priority {priority} set to '{node}' from '{parent}'"
                    .format(
                        priority=priority,
                        node=child_identifier,
                        parent=identifier
                    )
                )

    wiz.history.record_action(
        wiz.symbol.GRAPH_PRIORITY_COMPUTATION_ACTION,
        graph=graph, priority_mapping=priority_mapping
    )

    return priority_mapping


def trim_unreachable_from_graph(graph, priority_mapping):
    """Remove unreachable nodes from *graph* based on *priority_mapping*.

    If a node within the *graph* does not have a priority, it means that it
    cannot be reached from the root level. It will then be lazily removed
    from the graph (the links are preserved to save on computing time).

    *graph* must be an instance of :class:`Graph`.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    """
    logger = mlog.Logger(__name__ + ".trim_unreachable_from_graph")

    for node in graph.nodes():
        if priority_mapping[node.identifier].get("priority") is None:
            logger.debug("Remove '{}'".format(node.identifier))
            graph.remove_node(node.identifier)


def sorted_from_priority(identifiers, priority_mapping):
    """Return sorted node *identifiers* based on *priority_mapping*.

    If a node identifier does not have a priority, it means that it cannot be
    reached from the root level. It will then not be included in the list
    returned.

    *identifiers* should be valid node identifiers.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    """
    _identifiers = filter(
        lambda _id: priority_mapping.get(_id, {}).get("priority"), identifiers
    )
    return sorted(
        _identifiers, key=lambda _id: priority_mapping[_id]["priority"]
    )


def extract_conflicted_nodes(graph, node):
    """Return all nodes from *graph* conflicting with *node*.

    A node from the *graph* is in conflict with the node *identifier* when
    its definition identifier is identical.

    *graph* must be an instance of :class:`Graph`.

    *node* should be a :class:`Node` instance.

    """
    nodes = (graph.node(_id) for _id in graph.conflicts())

    return [
        _node for _node in nodes
        if _node.definition == node.definition
        and _node.identifier != node.identifier
    ]


def combined_requirements(graph, nodes, priority_mapping):
    """Return combined requirements from *nodes* in *graph*.

    *graph* must be an instance of :class:`Graph`.

    *nodes* should be a list of :class:`Node` instances.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    Raise :exc:`wiz.exception.GraphResolutionError` if requirements cannot
    be combined.

    """
    requirement = None

    for node in nodes:
        _requirement = graph.link_requirement(
            node.identifier, priority_mapping[node.identifier]["parent"]
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


def extract_parents(graph, nodes):
    """Return set of parent identifiers from *nodes*.

    *graph* must be an instance of :class:`Graph`.

    *nodes* should be a list of :class:`Node` instances.

    """
    identifiers = set()

    for node in nodes:
        for parent_identifier in node.parent_identifiers:
            if parent_identifier == graph.ROOT:
                continue

            # Filter out non existing nodes from incoming.
            parent_node = graph.node(parent_identifier)
            if parent_node is None:
                continue

            parent_identifier = parent_node.identifier
            identifiers.add(parent_identifier)

    return identifiers


def remove_node_and_relink(graph, node, identifiers, requirement):
    """Remove *node* from *graph* and relink node's parents to *identifiers*

    When creating the new links, the same weight connecting the *node* to its
    parents is being used. *requirement* indicate the new requirement link for
    all new links.

    *graph* must be an instance of :class:`Graph`.

    *node* should be a :class:`Node` instance.

    *identifiers* should be valid node identifiers.

    *requirement* should be a :class:`packaging.requirements.Requirement`
    instance.

    """
    graph.remove_node(node.identifier)

    for parent_identifier in node.parent_identifiers:
        if not graph.exists(parent_identifier):
            continue

        weight = graph.link_weight(node.identifier, parent_identifier)

        for _identifier in identifiers:
            graph.create_link(
                _identifier,
                parent_identifier,
                requirement,
                weight=weight
            )


def extract_ordered_packages(graph, priority_mapping):
    """Return sorted list of packages from *graph*.

    Best matching :class:`~wiz.package.Package` instances are
    extracted from each node instance and added to the list.

    *priority_mapping* is a mapping indicating the lowest possible priority
    of each node identifier from the root level of the graph with its
    corresponding parent node identifier.

    """
    logger = mlog.Logger(__name__ + ".extract_ordered_packages")

    packages = []

    for node in sorted(
        graph.nodes(),
        key=lambda n: priority_mapping[n.identifier].items(),
        reverse=True
    ):
        packages.append(node.package)

    logger.debug(
        "Sorted packages: {}".format(
            ", ".join([package.identifier for package in packages])
        )
    )

    wiz.history.record_action(
        wiz.symbol.GRAPH_PACKAGES_EXTRACTION_ACTION,
        graph=graph, packages=packages
    )

    return packages


class Graph(object):
    """Requirement Graph."""

    #: Identify the root of the graph
    ROOT = "root"

    def __init__(
        self, resolver, node_mapping=None, definition_mapping=None,
        constraint_mapping=None, variant_mapping=None, link_mapping=None
    ):
        """Initialise Graph.

        *resolver* should be an instance of :class:`Resolver`.

        *node_mapping* can be an initial mapping of nodes organised node
        identifier.

        *definition_mapping* can be an initial mapping of node identifier sets
        organised per definition identifier.

        *constraint_mapping* can be an initial mapping of :class:`Constraint`
        instances organised per definition identifier.

        *variant_mapping* can be an initial mapping of node identifiers with
        variant organised per definition identifier.

        *link_mapping* can be an initial mapping of node identifiers
        association.

        """
        self._logger = mlog.Logger(__name__ + ".Graph")
        self._resolver = resolver
        self._identifier = uuid.uuid4().hex

        # All nodes created per node identifier.
        self._node_mapping = node_mapping or {}

        # Set of node identifiers organised per definition identifier.
        self._definition_mapping = definition_mapping or {}

        # List of constraint instances organised per definition identifier.
        self._constraint_mapping = constraint_mapping or {}

        # List of identifiers with variant organised per definition identifier.
        self._variant_mapping = variant_mapping or {}

        # Record the weight of each link in the graph.
        self._link_mapping = link_mapping or {}

    @property
    def identifier(self):
        """Return unique graph identifier."""
        return self._identifier

    def to_dict(self):
        """Return corresponding dictionary."""
        return {
            "identifier": self.identifier,
            "node": {
                _id: node.to_dict() for _id, node
                in self._node_mapping.items()
            },
            "definition": {
                _id: sorted(node_ids) for _id, node_ids
                in self._definition_mapping.items()
            },
            "link": copy.deepcopy(self._link_mapping),
            "variants": self._variant_mapping.values(),
            "constraint": {
                _id: [constraint.to_dict() for constraint in constraints]
                for _id, constraints in self._constraint_mapping.items()
            }
        }

    def copy(self):
        """Return a copy of the graph."""
        return Graph(
            self._resolver,
            node_mapping=copy.deepcopy(self._node_mapping),
            definition_mapping=copy.deepcopy(self._definition_mapping),
            constraint_mapping=copy.deepcopy(self._constraint_mapping),
            variant_mapping=copy.deepcopy(self._variant_mapping),
            link_mapping=copy.deepcopy(self._link_mapping)
        )

    def node(self, identifier):
        """Return node from *identifier*."""
        return self._node_mapping.get(identifier)

    def nodes(self):
        """Return all nodes in the graph."""
        return self._node_mapping.values()

    def exists(self, identifier):
        """Indicate whether the node *identifier* is in the graph."""
        return identifier in self._node_mapping.keys()

    def variant_mapping(self):
        """Return variant groups organised per definition identifier.

        A variant group list should contain at least more than one node
        identifier which belongs at least to two different variant names.

        The mapping should be in the form of::

            {
                "foo": ["foo[V1]==0.1.0", "foo[V2]==0.1.0"],
                "bar": ["bar[V1]==2.1.5", "bar[V2]==2.2.0", "bar[V2]==2.1.0"]
            }

        """
        mapping = {}

        for definition_identifier, identifiers in self._variant_mapping.items():
            variant_names = set([
                self._node_mapping[identifier].variant_name
                for identifier in identifiers
            ])

            if len(variant_names) > 1:
                mapping[definition_identifier] = identifiers

        return mapping

    def outcoming(self, identifier):
        """Return outcoming node identifiers for node *identifier*."""
        return [
            identifier for identifier
            in self._link_mapping.get(identifier, {}).keys()
            if self.exists(identifier)
        ]

    def link_weight(self, identifier, parent_identifier):
        """Return weight from link between *parent_identifier* and *identifier*.
        """
        return self._link_mapping[parent_identifier][identifier]["weight"]

    def link_requirement(self, identifier, parent_identifier):
        """Return requirement from link between *parent_identifier* and
        *identifier*.

        This should be a :class:`packaging.requirements.Requirement` instance.

        """
        return self._link_mapping[parent_identifier][identifier]["requirement"]

    def conflicts(self):
        """Return conflicting nodes identifiers instances.

        A conflict appears when several nodes are found for a single
        definition identifier.

        """
        conflicted = []

        for identifiers in self._definition_mapping.values():
            _identifiers = [
                identifier for identifier in identifiers
                if self.exists(identifier)
            ]

            if len(_identifiers) > 1:
                conflicted += _identifiers

        return conflicted

    def update_from_requirements(self, requirements):
        """Update graph from *requirements*.

        *requirements* should be a list of
        class:`packaging.requirements.Requirement` instances ordered from the
        most important to the least important.

        One or several :class:`~wiz.package.Package` instances will be
        extracted from  *requirements* and :class:`Node` instances will be added
        to graph accordingly. The process will be repeated recursively for
        dependent requirements from newly created packages.

        Package's requirement are traversed with a `Breadth-first search
        <https://en.wikipedia.org/wiki/Breadth-first_search>`_ algorithm so that
        potential errors are raised for top-level packages first.

        Constraint packages will be recorded as :class:`Constraint` instances.
        Corresponding packages will be added to the graph only if at least one
        package with the same definition identifier has previously been added
        to the graph.

        """
        queue = _queue.Queue()

        # Fill up queue from constraint and update the graph accordingly.
        for index, requirement in enumerate(requirements):
            queue.put({"requirement": requirement, "weight": index + 1})

        self._update_from_queue(queue)

        # If constraints have been found, identify those which have
        # corresponding definition identifier in the graph and add it to the
        # queue to convert them into nodes.

        constraints_needed = self._constraints_identified_in_graph()

        while len(constraints_needed) > 0:
            for constraint in constraints_needed:
                queue.put({
                    "requirement": constraint.requirement,
                    "parent_identifier": constraint.parent_identifier,
                    "weight": constraint.weight
                })

            self._update_from_queue(queue)

            # Check if other new constraints need to be added to graph after
            # updating graph with previous constraints.
            constraints_needed = self._constraints_identified_in_graph()

    def _constraints_identified_in_graph(self):
        """Return :class:`Constraint` instances which should be added to graph.

        A constraint should be added to the graph once its definition identifier
        is found in the graph. The constraints returned will be removed from
        constraint mapping recorded by graph.

        """
        constraints = []

        for identifier in self._constraint_mapping.keys():
            if identifier in self._definition_mapping.keys():
                constraints += self._constraint_mapping[identifier]
                del self._constraint_mapping[identifier]

        self._logger.debug(
            "Constraints which needs to be added to the graph: {}".format(
                [str(constraint.requirement) for constraint in constraints]
            )
        )
        return constraints

    def _update_from_queue(self, queue):
        """Recursively update graph from data contained in *queue*.

        *queue* should be a :class:`Queue` instance.

        """
        while not queue.empty():
            data = queue.get()

            # The queue will be augmented with all dependent requirements.
            self._update_from_requirement(
                data.get("requirement"), queue,
                parent_identifier=data.get("parent_identifier"),
                weight=data.get("weight")
            )

    def _update_from_requirement(
        self, requirement, queue, parent_identifier=None, weight=1
    ):
        """Update graph from *requirement* and return updated *queue*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *queue* should be a :class:`Queue` instance that will be updated with
        all dependent requirements data.

        *parent_identifier* can indicate the identifier of a parent node.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. The lesser this number, the higher is
        the importance of the link. Default is 1.

        """
        self._logger.debug("Update from requirement: {}".format(requirement))

        # Get packages from requirement.
        packages = wiz.package.extract(
            requirement, self._resolver.definition_mapping
        )

        # Create a node for each package if necessary.
        for package in packages:
            if not self.exists(package.identifier):
                self._create_node_from_package(package)

                # Update queue with dependent requirement.
                for index, _requirement in enumerate(package.requirements):
                    queue.put({
                        "requirement": _requirement,
                        "parent_identifier": package.identifier,
                        "weight": index + 1
                    })

                # Record constraints so that it could be added later to the
                # graph as nodes if necessary.
                for index, _requirement in enumerate(package.constraints):
                    self._constraint_mapping.setdefault(_requirement.name, [])
                    self._constraint_mapping[_requirement.name].append(
                        Constraint(
                            _requirement, package.identifier, weight=index + 1
                        )
                    )

            node = self.node(package.identifier)
            node.add_parent(parent_identifier or self.ROOT)

            # Create link with requirement and weight.
            self.create_link(
                node.identifier,
                parent_identifier or self.ROOT,
                requirement,
                weight=weight
            )

    def _create_node_from_package(self, package):
        """Create node in graph from *package*.

        *package* should be a :class:`~wiz.package.Package` instance.

        """
        self._logger.debug("Adding package: {}".format(package.identifier))
        self._node_mapping[package.identifier] = Node(package)

        _definition_id = package.definition_identifier

        # Record variant per unique key identifier if necessary.
        if package.variant_name is not None:
            self._variant_mapping.setdefault(_definition_id, [])
            if package.identifier not in self._variant_mapping[_definition_id]:
                self._variant_mapping[_definition_id].append(package.identifier)

        # Record node identifiers per package to identify conflicts.
        self._definition_mapping.setdefault(_definition_id, set())
        self._definition_mapping[_definition_id].add(package.identifier)

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODE_CREATION_ACTION,
            graph=self, node=self._node_mapping[package.identifier].identifier
        )

    def create_link(
        self, identifier, parent_identifier, requirement, weight=1
    ):
        """Add dependency link from *parent_identifier* to *identifier*.

        *identifier* is the identifier of the package which is added to the
        dependency graph.

        *parent_identifier* is the identifier of the targeted package which
        must be linked to the new *identifier*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *weight* is a number which indicate the importance of the dependency
        link. The lesser this number, the higher is the importance of the link.
        Default is 1.

        Raise :exc:`wiz.exception.IncorrectEnvironment` is *package*
        identifier has already be set for this *parent*.

        """
        self._logger.debug(
            "Add dependency link from '{parent}' to '{child}'".format(
                parent=parent_identifier, child=identifier
            )
        )

        self._link_mapping.setdefault(parent_identifier, {})

        if identifier in self._link_mapping[parent_identifier].keys():
            raise wiz.exception.IncorrectDefinition(
                "There cannot be several dependency links to '{child}' from "
                "'{parent}'.".format(parent=parent_identifier, child=identifier)
            )

        link = {"requirement": requirement, "weight": weight}
        self._link_mapping[parent_identifier][identifier] = link

        # Record link creation to history if necessary.
        wiz.history.record_action(
            wiz.symbol.GRAPH_LINK_CREATION_ACTION,
            graph=self,
            parent=parent_identifier,
            child=identifier,
            weight=weight,
            requirement=requirement
        )

    def remove_node(self, identifier, record=True):
        """Remove node from the graph.

        *record* can indicate whether the node removal action should be recorded
        to the history. Usually this flag should only be turned off during the
        graph division process as the graph themselves are not recorded before
        the removal process.

        .. warning::

            A lazy deletion is performed as the links are not deleted to save on
            performance.

        """
        del self._node_mapping[identifier]

        if record:
            wiz.history.record_action(
                wiz.symbol.GRAPH_NODE_REMOVAL_ACTION,
                graph=self, node=identifier
            )

    def reset_variants(self):
        """Reset list of variant node identifiers .

        .. warning::

            A lazy deletion is performed as only the variant identifiers are
            deleted, but not the nodes themselves.

        """
        self._variant_mapping = {}


class Node(object):
    """Representation of an element of the :class:`Graph`.

    It encapsulates one :class:`~wiz.package.Package` instance with all parent
    package identifiers.

    """

    def __init__(self, package):
        """Initialise Node.

        *package* indicates a :class:`~wiz.package.Package` instance.

        """
        self._package = package
        self._parent_identifiers = set()

    @property
    def definition(self):
        """Return definition identifier of the node."""
        return self._package.definition_identifier

    @property
    def identifier(self):
        """Return identifier of the node.

        .. note::

            The node identifier is the same as the embedded
            :class:`~wiz.package.Package` instance identifier.

        """
        return self._package.identifier

    @property
    def variant_name(self):
        """Return variant name of the node.

        Return the variant name of the embedded
        :class:`~wiz.package.Package` instance. If the package does not have a
        variant, None is returned.

        """
        return self._package.variant_name

    @property
    def package(self):
        """Return :class:`~wiz.package.Package` encapsulated."""
        return self._package

    @property
    def parent_identifiers(self):
        """Return set of parent identifiers."""
        return self._parent_identifiers

    def add_parent(self, identifier):
        """Add *identifier* as a parent to the node."""
        self._parent_identifiers.add(identifier)

    def to_dict(self):
        """Return corresponding dictionary."""
        return {
            "package": self._package.to_dict(serialize_content=True),
            "parents": list(self._parent_identifiers)
        }


class Constraint(object):
    """Representation of a constraint mapping within the :class:`Graph`.

    It encapsulates one :class:`packaging.requirements.Requirement` instance,
    its parent package identifier and a weight number.

    A constraint will be converted into one or several :class:`Node` instances
    as soon as the corresponding definition identifier is found in the graph.

    For instance, if a constraint has a requirement such as
    `foo >= 0.1.0, < 0.2.0`, it will be added to the graph only if another
    package from the `foo` definition(s) has been previously added to the graph.

    """

    def __init__(self, requirement, parent_identifier, weight=1):
        """Initialize Constraint.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *parent_identifier* can indicate the identifier of a parent node.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. Default is 1.

        """
        self._requirement = requirement
        self._parent_identifier = parent_identifier
        self._weight = weight

    @property
    def requirement(self):
        """Return :class:`packaging.requirements.Requirement` instance."""
        return self._requirement

    @property
    def parent_identifier(self):
        """Return parent identifier."""
        return self._parent_identifier

    @property
    def weight(self):
        """Return weight number."""
        return self._weight

    def to_dict(self):
        """Return corresponding dictionary."""
        return {
            "requirement": self._requirement,
            "parent_identifier": self._parent_identifier,
            "weight": self._weight,
        }


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

    def empty(self):
        """Indicate whether the mapping is empty."""
        return len(self.keys()) == 0

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

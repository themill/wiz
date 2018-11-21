# :coding: utf-8

import copy
import itertools
import uuid
from collections import Counter
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
    """Graph resolver class.

    Compute a ordered list of packages from an initial list of
    :class:`packaging.requirements.Requirement` instances::

        >>> from packaging.requirements import Requirement
        >>> resolver = Resolver()
        >>> resolver.compute_packages(Requirement("foo"), Requirement("bar"))

        [Package("foo"), Package("bar"), Package("bim"), Package("baz")]

    A :class:`Graph` is instantiated with dependent requirements from initial
    requirements (e.g. "foo" requires "bim" and "bim" requires "bar").

    If several variants of one package definition are in the graph, the graph
    must be divided in as many graphs as there are variants. If several
    conflicting variant groups are in the graph, the number of graph division
    is equal to the multiplication of each variant group size. For instance, 24
    graph divisions would be necessary for the following example (3 x 2 x 4)::

        >>> graph = Graph(resolver)
        >>> graph.update_from_requirements(
        ...     Requirement("foo"), Requirement("bar"), Requirement("baz")
        ... )
        >>> graph.variant_mapping()

        {
            "foo": ["foo[V3]", "foo[V2]", "foo[V1]"],
            "bar": ["bar[V2]", "bar[V1]"],
            "foo": ["baz[V4]", "baz[V3]", "baz[V2]", "baz[V1]"],
        }

    Instead of directly dividing the graph 24 times, a list of trimming
    combination is generated to figure out the order of the graph division and
    the node identifiers which should be remove during each division. For
    the example above, the first graph will be computed with "foo[V3]",
    "bar[V2]" and "baz[V4]" so all other variant conflicts should be removed.
    The second graph is generated with "foo[V3]", "bar[V2]" and "baz[V3]" only
    if the first graph cannot be resolved.

    The resolution process of the graph ensure that only one version of each
    package definition is kept. If several versions of one package definition
    are in a graph, their corresponding requirement will be analyzed to ensure
    that they are compatible.

    .. code-block:: none

        - 'foo==0.5.0' is required by 'foo<1';
        - 'foo==1.0.0' is required by 'foo';
        - The version '0.5.0' is matching both requirements;
        - Requirements 'foo<1' and 'foo' are seen as compatible.

    The graph cannot be resolved if two requirements are incompatibles.

    If the requirements are compatibles, they will be combined to figure out
    which nodes should be removed from the graph. The requirement combination
    can lead to the addition of new nodes to the graph which can lead to further
    graph divisions.

    """

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

        # Record mapping indicating the shortest possible distance of each node
        # identifier from the root level of the graph with corresponding
        # parent node identifier.
        self._distance_mapping = None

        # Iterator which yield the next graph to resolve with a list of
        # conflicting variant node identifiers to remove before instantiation.
        self._iterator = iter([])

    @property
    def definition_mapping(self):
        """Return mapping of all available definitions."""
        return self._definition_mapping

    def compute_packages(self, requirements):
        """Resolve requirements graphs and return list of packages.

        *requirements* should be a list of
        :class:`packaging.requirements.Requirement` instances.

        """
        self._initiate(requirements)

        # Store latest exception to raise if necessary.
        latest_error = None

        while True:
            graph = self._fetch_next_graph()
            if graph is None:
                raise latest_error

            try:
                self._resolve_conflicts(graph)

            except wiz.exception.WizError as error:
                wiz.history.record_action(
                    wiz.symbol.GRAPH_RESOLUTION_FAILURE_ACTION,
                    graph=graph, error=error
                )

                self._logger.debug("Failed to resolve graph: {}".format(error))
                latest_error = error

            else:
                distance_mapping, _ = self._fetch_distance_mapping(graph)
                return extract_ordered_packages(graph, distance_mapping)

    def _initiate(self, requirements):
        """Initialize iterator with a graph created from *requirement*.

        *requirements* should be a list of
        class:`packaging.requirements.Requirement` instances.

        """
        graph = Graph(self)

        wiz.history.record_action(
            wiz.symbol.GRAPH_CREATION_ACTION,
            graph=graph, requirements=requirements
        )

        # Update the graph.
        graph.update_from_requirements(requirements)

        # Reset the iterator.
        self._iterator = iter([])

        # Initialize combinations or simply add graph to iterator.
        if not self._extract_combinations(graph):
            self._iterator = iter([(graph, [])])

    def _fetch_distance_mapping(self, graph):
        """Return tuple with distance mapping and boolean update indicator.

        If no distance mapping is available, a new one is generated from
        *graph*. The boolean update indicator is True only if a new distance
        mapping is generated.

        """
        updated = False

        if self._distance_mapping is None:
            self._distance_mapping = compute_distance_mapping(graph)
            updated = True

        return self._distance_mapping, updated

    def _fetch_next_graph(self):
        """Return next graph computed from the iterator."""
        try:
            graph, nodes_to_remove = next(self._iterator)
        except StopIteration:
            return

        self._logger.debug(
            "Generate graph without following nodes: {!r}".format(
                nodes_to_remove
            )
        )

        # To prevent mutating any copy of the instance.
        _graph = copy.deepcopy(graph)

        # Reset the distance mapping for new graph.
        self._distance_mapping = None

        for identifier in nodes_to_remove:
            _graph.remove_node(identifier, record=False)

        wiz.history.record_action(
            wiz.symbol.GRAPH_COMBINATION_EXTRACTION_ACTION,
            graph=_graph, removed_nodes=nodes_to_remove
        )

        return _graph

    def _extract_combinations(self, graph):
        """Extract possible combinations from variant conflicts in *graph*.

        Return a boolean value indicating whether combination generator has been
        added to the iterator.

        *graph* must be an instance of :class:`Graph`.

        """
        variant_mapping = graph.variant_mapping()
        if len(variant_mapping) == 0:
            self._logger.debug(
                "No package variants are conflicting in the graph."
            )
            return False

        # Record all definition identifiers which led to graph division.
        self._definitions_with_variants.extend(variant_mapping.keys())

        distance_mapping, _ = self._fetch_distance_mapping(graph)

        # Order the variant groups in ascending order of distance from the root
        # level of the graph. We can assume that the first identifier of each
        # group is the node with the shortest distance as the graph has been
        # updated using a Breadth First Search algorithm.
        variant_groups = sorted(
            variant_mapping.values(),
            key=lambda _group: distance_mapping[_group[0]].get("distance"),
        )

        self._logger.debug(
            "The following variant groups are conflicting: {!r}".format(
                variant_groups
            )
        )

        wiz.history.record_action(
            wiz.symbol.GRAPH_VARIANT_CONFLICTS_IDENTIFICATION_ACTION,
            graph=graph, variant_groups=variant_groups
        )

        self._iterator = itertools.chain(
            generate_variant_combinations(graph, variant_groups),
            self._iterator
        )
        return True

    def _resolve_conflicts(self, graph):
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
            wiz.symbol.GRAPH_VERSION_CONFLICTS_IDENTIFICATION_ACTION,
            graph=graph, conflicting=conflicts
        )

        while True:
            distance_mapping, updated = self._fetch_distance_mapping(graph)

            # Update graph and conflicts to remove all unreachable nodes if
            # distance mapping have been updated.
            if updated:
                trim_unreachable_from_graph(graph, distance_mapping)
                conflicts = updated_by_distance(conflicts, distance_mapping)

            # If no nodes are left in the queue, exit the loop. The graph
            # is officially resolved. Hooray!
            if len(conflicts) == 0:
                return

            # Pick up the nearest conflicting node identifier.
            identifier = conflicts.pop()
            node = graph.node(identifier)

            # Identify nodes conflicting with this node.
            conflicting_nodes = extract_conflicting_nodes(graph, node)

            # Compute valid node identifier from combined requirements.
            requirement = combined_requirements(
                graph, [node] + conflicting_nodes, distance_mapping
            )

            # Query packages from combined requirement.
            try:
                packages = wiz.package.extract(
                    requirement, self._definition_mapping
                )
            except wiz.exception.RequestNotFound:
                _parents = extract_parents(graph, [node] + conflicting_nodes)

                # Discard conflicting nodes if parents are themselves
                # conflicting.
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

                # The graph changed in a way that can affect the distances of
                # other nodes, so the distance mapping is discarded.
                self._distance_mapping = None

                # Identify whether some of the newly extracted packages are not
                # in the list of conflicting nodes to decide if the graph should
                # be updated.
                _identifiers = set(identifiers).difference(
                    set([_node.identifier for _node in conflicting_nodes])
                )

                # If not all extracted packages are identified as conflicts, it
                # means that variants need to be added to the  graph. If
                # variants from this definition identifier have  already been
                # processed, the update is skipped.
                if (
                    len(_identifiers) == len(conflicting_nodes) and
                    node.definition not in self._definitions_with_variants
                ):
                    self._logger.debug(
                        "Add to graph: {}".format(", ".join(_identifiers))
                    )
                    graph.update_from_requirements([requirement])

                    # Update conflict list if necessary.
                    conflicts = list(set(conflicts + graph.conflicts()))

                    # If the updated graph contains conflicting variants, the
                    # relevant combination must be extracted, therefore the
                    # current combination cannot be resolved.
                    if self._extract_combinations(graph):
                        raise wiz.exception.GraphResolutionError(
                            "The current graph has conflicting variants."
                        )


def compute_distance_mapping(graph):
    """Return distance mapping for each node of *graph*.

    The mapping indicates the shortest possible distance of each node
    identifier from the :attr:`root <Graph.ROOT>` level of the *graph* with
    corresponding parent node identifier.

    The distance is defined by the sum of the weights from each node to the
    :attr:`root <Graph.ROOT>` level of the *graph*.

    *graph* must be an instance of :class:`Graph`.

    This is using `Dijkstra's shortest path algorithm
    <https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm>`_.

    .. note::

        When a node is being visited twice, the path with the shortest
        distance is being kept.

    """
    logger = mlog.Logger(__name__ + ".compute_distance_mapping")
    logger.debug("Compute distance mapping...")

    # Initiate mapping
    distance_mapping = {
        node.identifier: {"distance": None, "parent": None}
        for node in graph.nodes()
    }

    distance_mapping[graph.ROOT] = {"distance": 0, "parent": graph.ROOT}

    queue = _DistanceQueue()
    queue[graph.ROOT] = 0

    while not queue.empty():
        identifier = queue.pop_smallest()
        current_distance = distance_mapping[identifier]["distance"]

        for child_identifier in graph.outcoming(identifier):
            distance = current_distance + graph.link_weight(
                child_identifier, identifier
            )

            # The last recorded distance of this node from the source
            last_distance = distance_mapping[child_identifier]["distance"]

            # If there is a currently recorded distance from the source and
            # this is superior than the distance of the node found, update
            # the current distance with the new one.
            if last_distance is None or last_distance > distance:
                distance_mapping[child_identifier] = {
                    "distance": distance, "parent": identifier
                }
                queue[child_identifier] = distance

                logger.debug(
                    "Distance {distance} set to '{node}' from '{parent}'"
                    .format(
                        distance=distance,
                        node=child_identifier,
                        parent=identifier
                    )
                )

    wiz.history.record_action(
        wiz.symbol.GRAPH_DISTANCE_COMPUTATION_ACTION,
        graph=graph, distance_mapping=distance_mapping
    )

    return distance_mapping


def generate_variant_combinations(graph, variant_groups):
    """Yield combinations of nodes identifiers to remove from *graph*.

    *graph* must be an instance of :class:`Graph`.

    *variant_groups* should be a list of node identifier lists. Each list
    contains node identifiers added to the *graph* in the order of importance
    which share the same definition identifier and variant identifier.

    After identifying and grouping version conflicts in each group, a cartesian
    product is performed on all groups in order to extract combinations of node
    variant that should be present in the graph at the same time.

    The trimming combination represents the inverse of this product, so that it
    identify the nodes to remove at each graph division::

        >>> variant_groups = [
        ...     ["foo[V3]", "foo[V2]", "foo[V1]"],
        ...     ["bar[V1]==1", "bar[V2]==1", "bar[V2]==2"]
        ... ]
        >>> list(generate_variant_combinations(graph, variant_groups))

        [
            (graph, ("foo[V2]", "foo[V1]", "bar[V2]==1", "bar[V2]==2")),
            (graph, ("foo[V2]", "foo[V1]", "bar[V1]==1")),
            (graph, ("foo[V3]", "foo[V1]", "bar[V2]==1", "bar[V2]==2")),
            (graph, ("foo[V3]", "foo[V1]", "bar[V1]==1")),
            (graph, ("foo[V3]", "foo[V2]", "bar[V2]==1", "bar[V2]==2")),
            (graph, ("foo[V3]", "foo[V2]", "bar[V1]==1"))
        ]

    """
    # Flatten list of identifiers
    identifiers = [_id for _group in variant_groups for _id in _group]

    # Convert each variant group into list of lists grouping conflicting nodes.
    # e.g. [A[V2]==1, A[V1]==1, A[V1]==2] -> [[A[V2]==1], [A[V1]==1, A[V1]==2]]
    _groups = []

    for _group in variant_groups:
        variant_mapping = {}

        for node_identifier in _group:
            node = graph.node(node_identifier)
            variant_mapping.setdefault(node.variant_name, [])
            variant_mapping[node.variant_name].append(node_identifier)
            variant_mapping[node.variant_name].sort(
                key=lambda _id: _group.index(_id)
            )

        _tuple_group = sorted(
            variant_mapping.values(),
            key=lambda group: _group.index(group[0])
        )
        _groups.append(_tuple_group)

    for combination in itertools.product(*_groups):
        _identifiers = [_id for _group in combination for _id in _group]
        yield (
            graph,
            tuple([_id for _id in identifiers if _id not in _identifiers])
        )


def trim_unreachable_from_graph(graph, distance_mapping):
    """Remove unreachable nodes from *graph* based on *distance_mapping*.

    If a node within the *graph* does not have a distance, it means that it
    cannot be reached from the :attr:`root <Graph.ROOT>` level of the *graph*.
    It will then be lazily removed from the graph (the links are preserved to
    save on computing time).

    *graph* must be an instance of :class:`Graph`.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    *graph* with its corresponding parent node identifier.

    """
    logger = mlog.Logger(__name__ + ".trim_unreachable_from_graph")

    for node in graph.nodes():
        if distance_mapping[node.identifier].get("distance") is None:
            logger.debug("Remove '{}'".format(node.identifier))
            graph.remove_node(node.identifier)


def updated_by_distance(identifiers, distance_mapping):
    """Return updated node *identifiers* according to *distance_mapping*.

    The node identifier list returned is sorted in ascending order of distance
    from the :attr:`root <Graph.ROOT>` level of the graph.

    If a node identifier does not have a distance, it means that it cannot be
    reached from the root level. It will then not be included in the list
    returned.

    *identifiers* should be valid node identifiers.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    graph with its corresponding parent node identifier.

    """
    _identifiers = filter(
        lambda _id: distance_mapping.get(_id, {}).get("distance"), identifiers
    )
    return sorted(
        _identifiers, key=lambda _id: distance_mapping[_id]["distance"]
    )


def extract_conflicting_nodes(graph, node):
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


def combined_requirements(graph, nodes, distance_mapping):
    """Return combined requirements from *nodes* in *graph*.

    *graph* must be an instance of :class:`Graph`.

    *nodes* should be a list of :class:`Node` instances.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    graph with its corresponding parent node identifier.

    Raise :exc:`wiz.exception.GraphResolutionError` if requirements cannot
    be combined.

    """
    requirement = None

    for node in nodes:
        _requirement = graph.link_requirement(
            node.identifier, distance_mapping[node.identifier]["parent"]
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
    """Return set of existing parent node identifiers from *nodes*.

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


def extract_ordered_packages(graph, distance_mapping):
    """Return sorted list of packages from *graph*.

    Best matching :class:`~wiz.package.Package` instances are
    extracted from each node instance and added to the list.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    graph with its corresponding parent node identifier.

    """
    logger = mlog.Logger(__name__ + ".extract_ordered_packages")

    packages = []

    for node in sorted(
        graph.nodes(),
        key=lambda n: distance_mapping[n.identifier].items(),
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

    def __init__(self, resolver):
        """Initialise Graph.

        *resolver* should be an instance of :class:`Resolver`.

        """
        self._logger = mlog.Logger(__name__ + ".Graph")
        self._resolver = resolver
        self._identifier = uuid.uuid4().hex

        # All nodes created per node identifier.
        self._node_mapping = {}

        # Record the weight of each link in the graph.
        self._link_mapping = {}

        # Set of node identifiers organised per definition identifier.
        self._identifiers_per_definition = {}

        # List of constraint instances organised per definition identifier.
        self._constraints_per_definition = {}

        # List of node identifiers with variant organised per definition
        # identifier.
        self._variants_per_definition = {}

        # Set of namespaces found in packages added.
        self._namespaces = set()

    def __deepcopy__(self, memo):
        """Ensure that only necessary element are copied in the new graph."""
        result = Graph(self._resolver)
        result._node_mapping = copy.deepcopy(self._node_mapping)
        result._link_mapping = copy.deepcopy(self._link_mapping)
        result._identifiers_per_definition = (
            copy.deepcopy(self._identifiers_per_definition)
        )
        result._constraints_per_definition = (
            copy.deepcopy(self._constraints_per_definition)
        )
        result._variants_per_definition = (
            copy.deepcopy(self._variants_per_definition)
        )

        result._namespaces = copy.deepcopy(self._namespaces)

        memo[id(self)] = result
        return result

    @property
    def identifier(self):
        """Return unique graph identifier."""
        return self._identifier

    def to_dict(self):
        """Return corresponding dictionary."""
        return {
            "identifier": self.identifier,
            "node_mapping": {
                _id: node.to_dict() for _id, node
                in self._node_mapping.items()
            },
            "link_mapping": copy.deepcopy(self._link_mapping),
            "identifiers_per_definition": {
                _id: sorted(node_ids) for _id, node_ids
                in self._identifiers_per_definition.items()
            },
            "constraints_per_definition": {
                _id: [constraint.to_dict() for constraint in constraints]
                for _id, constraints in self._constraints_per_definition.items()
            },
            "variants_per_definition": self._variants_per_definition,
            "namespaces": sorted(self._namespaces),
        }

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

        The variant group list contains unique identifiers and is sorted
        following two criteria: First by the number of occurrences of each node
        identifier in the graph and second by the variant index defined in the
        package definition.

        The mapping should be in the form of::

            {
                "foo": ["foo[V1]==0.1.0", "foo[V2]==0.1.0"],
                "bar": ["bar[V1]==2.1.5", "bar[V2]==2.2.0", "bar[V2]==2.1.0"]
            }

        """
        mapping = {}

        for definition_identifier in self._variants_per_definition.keys():
            identifiers = self._variants_per_definition[definition_identifier]
            variant_names = set([
                self._node_mapping[identifier].variant_name
                for identifier in identifiers
            ])

            if len(variant_names) <= 1:
                continue

            count = Counter(identifiers)
            mapping[definition_identifier] = sorted(
                set(identifiers),
                key=lambda _id: (-count[_id], identifiers.index(_id))
            )

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
        conflicting = []

        for identifiers in self._identifiers_per_definition.values():
            _identifiers = [
                identifier for identifier in identifiers
                if self.exists(identifier)
            ]

            if len(_identifiers) > 1:
                conflicting += _identifiers

        return conflicting

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

        wiz.history.record_action(
            wiz.symbol.GRAPH_UPDATE_ACTION,
            graph=self, requirements=requirements
        )

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

        for identifier in self._constraints_per_definition.keys():
            if identifier in self._identifiers_per_definition.keys():
                constraints += self._constraints_per_definition[identifier]
                del self._constraints_per_definition[identifier]

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
            requirement, self._resolver.definition_mapping,
            namespaces=self._namespaces
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
                    _identifier = _requirement.name
                    self._constraints_per_definition.setdefault(_identifier, [])
                    self._constraints_per_definition[_identifier].append(
                        Constraint(
                            _requirement, package.identifier, weight=index + 1
                        )
                    )

            else:
                # Update variant mapping if necessary
                self._update_variant_mapping(package.identifier)

            node = self._node_mapping[package.identifier]
            node.add_parent(parent_identifier or self.ROOT)

            # Record namespace if necessary to provide hints for other requests.
            if package.namespace is not None:
                self._namespaces.add(package.namespace)

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

        # Record node identifiers per package to identify conflicts.
        _definition_id = package.definition_identifier
        self._identifiers_per_definition.setdefault(_definition_id, set())
        self._identifiers_per_definition[_definition_id].add(package.identifier)

        # Record variant per unique key identifier if necessary.
        self._update_variant_mapping(package.identifier)

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODE_CREATION_ACTION,
            graph=self, node=package.identifier
        )

    def _update_variant_mapping(self, identifier):
        """Update variant mapping according to node *identifier*.
        """
        node = self._node_mapping[identifier]
        if node.variant_name is None:
            return

        self._variants_per_definition.setdefault(node.definition, [])
        self._variants_per_definition[node.definition].append(identifier)

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
        self._variants_per_definition = {}


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


class _DistanceQueue(dict):
    """Distance mapping which can be used as a queue.

    Distances are cumulated weights computed between each node and the
    :attr:`root of the graph <Graph.ROOT>`.

    Keys of the dictionary are node identifiers added into a queue, and
    values are their respective distances.

    The advantage over a standard heapq-based distance queue is that distances
    of node identifiers can be efficiently updated (amortized O(1)).

    .. note::

        Inspired by Matteo Dell'Amico's implementation:
        https://gist.github.com/matteodellamico/4451520

    """

    def __init__(self, *args, **kwargs):
        """Initialise mapping and build heap."""
        super(_DistanceQueue, self).__init__(*args, **kwargs)
        self._build_heap()

    def _build_heap(self):
        """Build the heap from mapping's keys and values."""
        self._heap = [
            (distance, identifier) for identifier, distance in self.items()
        ]
        heapify(self._heap)

    def __setitem__(self, identifier, distance):
        """Set *distance* value for *identifier* item.

        *identifier* should be a node identifier.

        *distance* should be a number indicating the importance of the node. A
        shorter distance from the graph root means that the node has a higher
        importance than nodes with longer distances.

        .. note::

            The distance is not removed from the heap since this would have a
            cost of O(n).

        """
        super(_DistanceQueue, self).__setitem__(identifier, distance)

        if len(self._heap) < 2 * len(self):
            heappush(self._heap, (distance, identifier))
        else:
            # When the heap grows larger than 2 * len(self), we rebuild it
            # from scratch to avoid wasting too much memory.
            self._build_heap()

    def empty(self):
        """Indicate whether the mapping is empty."""
        return len(self.keys()) == 0

    def pop_smallest(self):
        """Return item with the shortest distance from graph root and remove it.

        Raises :exc:`IndexError` if the object is empty.

        """

        heap = self._heap
        distance, identifier = heappop(heap)

        while identifier not in self or self[identifier] != distance:
            distance, identifier = heappop(heap)

        del self[identifier]
        return identifier

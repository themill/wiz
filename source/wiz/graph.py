# :coding: utf-8

import copy
import itertools
import uuid
import signal
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

    def __init__(self, definition_mapping, timeout=300):
        """Initialise Resolver with *requirements*.

        *definition_mapping* is a mapping regrouping all available definitions
        associated with their unique identifier.

        *timeout* is the max time to expire before the resolve process is being
        cancelled (in seconds). Default is 5 minutes.

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

        # Time limit for the resolution process.
        self._timeout = timeout

    @property
    def definition_mapping(self):
        """Return mapping of all available definitions."""
        return self._definition_mapping

    def compute_packages(self, requirements):
        """Resolve requirements graphs and return list of packages.

        *requirements* should be a list of
        :class:`packaging.requirements.Requirement` instances.

        Raises :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
        resolved in time.

        """
        with Timeout(self._timeout):
            return self._compute_packages(requirements)

    def _compute_packages(self, requirements):
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
                # Raise error if a conflict in graph cannot be solved.
                self._resolve_conflicts(graph)

                # Compute distance mapping if necessary.
                distance_mapping, _ = self._fetch_distance_mapping(graph)

                # Raise remaining error found in graph if necessary.
                validate(graph, distance_mapping)

                # Extract packages ordered by descending order of distance.
                return extract_ordered_packages(graph, distance_mapping)

            except wiz.exception.WizError as error:
                wiz.history.record_action(
                    wiz.symbol.GRAPH_RESOLUTION_FAILURE_ACTION,
                    graph=graph, error=error
                )

                self._logger.debug("Failed to resolve graph: {}".format(error))
                latest_error = error

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
        graph.update_from_requirements(requirements, graph.ROOT)

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
        if not variant_mapping:
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
        conflicts = graph.conflicting_identifiers()
        if not conflicts:
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
            # there are remaining conflicts in the graph or if distance mapping
            # have been updated.
            if updated and conflicts:
                trim_unreachable_from_graph(graph, distance_mapping)
                conflicts = updated_by_distance(conflicts, distance_mapping)

            # If no nodes are left in the queue, exit the loop. The graph
            # is officially resolved. Hooray!
            if not conflicts:
                return

            # Pick up the furthest conflicting node identifier so that nearest
            # node have priorities.
            identifier = conflicts.pop()
            node = graph.node(identifier)

            # Identify nodes conflicting with this node.
            conflicting_nodes = extract_conflicting_nodes(graph, node)

            # Compute valid node identifier from combined requirements.
            requirement = combined_requirements(
                graph, [node] + conflicting_nodes
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

            # If current node is not in the packages extracted from the combined
            # requirement, it needs to be removed from the graph.
            identifiers = [package.qualified_identifier for package in packages]

            if identifier not in identifiers:
                self._logger.debug("Remove '{}'".format(identifier))
                graph.remove_node(node.identifier)

                # The graph changed in a way that can affect the distances of
                # other nodes, so the distance mapping cached is discarded.
                self._distance_mapping = None

                # Update the graph with new nodes if necessary. Discard the
                # whole graph if a variant division is needed.
                updated = self._update_graph_from_conflict(
                    graph, packages, requirement, conflicting_nodes
                )

                # Relink node parents to package identifiers.
                relink_parents(graph, node, identifiers, requirement)

                if updated:
                    # Update conflict list if necessary.
                    conflicts = list(
                        set(conflicts + graph.conflicting_identifiers())
                    )

                    # If the updated graph contains conflicting variants, the
                    # relevant combination must be extracted, therefore the
                    # current graph combination cannot be resolved.
                    if self._extract_combinations(graph):
                        raise wiz.exception.GraphResolutionError(
                            "The current graph has conflicting variants."
                        )

            # Search and trim invalid nodes from graph if conditions are no
            # longer fulfilled. If so reset the distance mapping.
            while trim_invalid_from_graph(graph, distance_mapping):
                self._distance_mapping = None

    def _update_graph_from_conflict(
        self, graph, packages, requirement, conflicting_nodes,
    ):
        """Update *graph* with new node(s) from *packages* if necessary.

        Return whether the graph has been updated.

        *graph* must be an instance of :class:`Graph`.

        *packages* must be a list of :class:`~wiz.package.Package` instances
        which are variants of the same definition identifier version. It can
        also be a unique package version without variants.

        *requirement* must be the :class:`packaging.requirements.Requirement`
        which led to the package extraction.

        *conflicting_nodes* should be a list of :class:`Node` instances
        representing conflicting version of a definition within the *graph*.

        *parent_identifiers* should be a list of package identifiers (or
        :attr:`root <Graph.ROOT>` which should be set as parents to the new
        nodes)

        .. note::

            If the *packages* list contains more than one item, it means that
            several variants of one definition version have been extracted. If
            not all extracted *packages* are identified in the
            *conflicting_nodes* list, it might be because the graph has already
            divided the graph for this particular definition identifier.

            We need all items from the *packages* list to be new and their
            definition identifier to be new so that it could be added to the
            graph.

        """
        # Extract common definition identifier.
        definition_identifier = packages[0].definition_identifier

        # Identify whether some of the newly extracted packages are not
        # in the list of conflicting nodes.
        identifiers = [package.qualified_identifier for package in packages]
        identifiers = set(identifiers).difference(
            set([_node.identifier for _node in conflicting_nodes])
        )

        # If all newly packages have the same number of variants (or no
        # variants at all) and the definition identifier hasn't been used to
        # divide the graph yet, it will be added to the graph.
        if (
            len(identifiers) == len(conflicting_nodes) and
            definition_identifier not in self._definitions_with_variants
        ):
            self._logger.debug(
                "Add to graph: {}".format(", ".join(identifiers))
            )

            for package in packages:
                graph.update_from_package(package, requirement)

            return True

        return False


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

    # Record variant node with error to prevent it being used more than once.
    blacklist = set()

    for combination in itertools.product(*_groups):
        _identifiers = [_id for _group in combination for _id in _group]

        # Skip combination which contains blacklisted node.
        if blacklist.intersection(_identifiers):
            continue

        yield (
            graph,
            tuple([_id for _id in identifiers if _id not in _identifiers])
        )

        # Update blacklist with error encountered in current combination.
        blacklist = set(_identifiers).intersection(graph.error_identifiers())


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


def trim_invalid_from_graph(graph, distance_mapping):
    """Remove invalid nodes from *graph* based on *distance_mapping*.

    Return boolean value indicating whether invalid nodes have been removed.

    If any packages that a node is conditioned by are no longer in the graph,
    the node is marked invalid and must be removed from the graph.

    *graph* must be an instance of :class:`Graph`.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    *graph* with its corresponding parent node identifier.

    """
    logger = mlog.Logger(__name__ + ".trim_invalid_from_graph")

    nodes_removed = False

    for node in graph.nodes():
        # Check if all conditions are still fulfilled.
        for requirement in node.package.conditions:
            identifiers = graph.find(requirement)

            if len(identifiers) == 0 or any(
                distance_mapping.get(identifier, {}).get("distance") is None
                for identifier in identifiers
            ):
                logger.debug(
                    "Remove '{}' as conditions are no longer "
                    "fulfilled".format(node.identifier)
                )
                graph.remove_node(node.identifier)
                nodes_removed = True
                break

    return nodes_removed


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
        lambda _id: distance_mapping.get(_id, {}).get("distance") is not None,
        identifiers
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
    nodes = (graph.node(_id) for _id in graph.conflicting_identifiers())

    return [
        _node for _node in nodes
        if _node.definition == node.definition
        and _node.identifier != node.identifier
    ]


def combined_requirements(graph, nodes):
    """Return combined requirements from *nodes* in *graph*.

    *graph* must be an instance of :class:`Graph`.

    *nodes* should be a list of :class:`Node` instances.

    Raise :exc:`wiz.exception.GraphResolutionError` if requirements cannot
    be combined.

    """
    requirement = None

    for node in nodes:
        _requirements = (
            graph.link_requirement(node.identifier, _identifier)
            for _identifier in node.parent_identifiers
            if _identifier is graph.ROOT or graph.exists(_identifier)
        )

        for _requirement in _requirements:
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


def sanitize_requirement(requirement, namespace):
    """Mutate package *requirement* according to the package *namespace*.

    This is necessary so that the requirement name is always qualified to
    prevent error when :func:`combining requirements <combined_requirements>`
    during the conflict resolution process.

    If the requirement "foo > 1" was used to fetch the package "namespace::foo",
    the requirement will be mutated to "namespace::foo > 1"

    On the other had, if the requirement "::bar==0.1.0" was used to fetch the
    package "bar" which doesn't have a namespace, the requirement will be
    mutated to "bar==0.1.0"

    """
    separator = wiz.symbol.NAMESPACE_SEPARATOR

    if namespace is not None and separator not in requirement.name:
        requirement.name = namespace + separator + requirement.name

    elif namespace is None and separator in requirement.name:
        requirement.name = requirement.name.rsplit(separator, 1)[-1]


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


def relink_parents(graph, node, identifiers, requirement):
    """Relink *node*'s parents to *identifiers*.

    When creating the new links, the same weight connecting the *node* to its
    parents is being used. *requirement* indicate the new requirement link for
    all new links.

    *graph* must be an instance of :class:`Graph`.

    *node* should be a :class:`Node` instance.

    *identifiers* should be valid node identifiers.

    *requirement* should be a :class:`packaging.requirements.Requirement`
    instance.

    """
    for parent_identifier in node.parent_identifiers:
        if (
            not graph.exists(parent_identifier) and
            not parent_identifier == graph.ROOT
        ):
            continue

        weight = graph.link_weight(node.identifier, parent_identifier)

        for _identifier in identifiers:
            # Add parent to node if node already exists in graph.
            _node = graph.node(_identifier)
            if _node is not None:
                _node.add_parent(parent_identifier)

            graph.create_link(
                _identifier,
                parent_identifier,
                requirement,
                weight=weight
            )


def validate(graph, distance_mapping):
    """Ensure that *graph* does not have remaining errors.

    The identifier nearest to the :attr:`root <Graph.ROOT>` level are analyzed
    first, and the first exception raised under one this identifier will be
    raised.

    *graph* must be an instance of :class:`Graph`.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    graph with its corresponding parent node identifier.

    An :exc:`wiz.exception.WizError` is raised if an error attached to the
    :attr:`root <Graph.ROOT>` level or any reachable node is found.

    """
    logger = mlog.Logger(__name__ + ".validate")

    errors = graph.error_identifiers()
    if not errors:
        logger.debug("No errors in the graph.")
        return

    logger.debug("Errors: {}".format(", ".join(errors)))

    wiz.history.record_action(
        wiz.symbol.GRAPH_ERROR_IDENTIFICATION_ACTION,
        graph=graph, errors=errors
    )

    # Updating identifier list from distance mapping automatically filter out
    # unreachable nodes.
    identifiers = updated_by_distance(errors, distance_mapping)
    if len(identifiers) == 0:
        raise wiz.exception.GraphResolutionError(
            "The resolution graph does not contain any valid packages."
        )

    # Pick up nearest node identifier which contains an error.
    identifier = identifiers[0]

    exceptions = graph.errors(identifier)
    logger.debug(
        "{} exception(s) raised under {}".format(len(exceptions), identifier)
    )

    # Raise first exception found when updating graph if necessary.
    raise exceptions[0]


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
        # Skip node if unreachable.
        if distance_mapping[node.identifier].get("distance") is None:
            continue

        # Otherwise keep the package.
        packages.append(node.package)

    logger.debug(
        "Sorted packages: {}".format(
            ", ".join([package.qualified_identifier for package in packages])
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

        # Record the weight and requirement of each link in the graph.
        self._link_mapping = {}

        # Set of node identifiers organised per definition identifier.
        self._identifiers_per_definition = {}

        # List of stored nodes with related conditions.
        self._conditioned_nodes = []

        # List of node identifiers with variant organised per definition
        # identifier.
        self._variants_per_definition = {}

        # :class:`collections.Counter` instance which record of occurrences of
        # namespaces from package included in the graph.
        # e.g. Counter({u'maya': 2, u'houdini': 1})
        self._namespace_count = Counter()

        # List of exception raised per node identifier.
        self._error_mapping = {}

    def __deepcopy__(self, memo):
        """Ensure that only necessary element are copied in the new graph."""
        result = Graph(self._resolver)
        result._node_mapping = copy.deepcopy(self._node_mapping)
        result._link_mapping = copy.deepcopy(self._link_mapping)
        result._identifiers_per_definition = (
            copy.deepcopy(self._identifiers_per_definition)
        )
        result._conditioned_nodes = copy.deepcopy(self._conditioned_nodes)
        result._variants_per_definition = (
            copy.deepcopy(self._variants_per_definition)
        )
        result._namespace_count = copy.deepcopy(self._namespace_count)
        result._error_mapping = copy.deepcopy(self._error_mapping)

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
            "conditioned_nodes": [
                stored_node.to_dict() for stored_node in self._conditioned_nodes
            ],
            "variants_per_definition": self._variants_per_definition,
            "namespace_count": dict(self._namespace_count),
            "error_mapping": {
                _id: [str(exception) for exception in exceptions]
                for _id, exceptions in self._error_mapping.items()
            },
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

    def find(self, requirement):
        """Return matching node identifiers in graph for *requirement*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        .. warning::

            Node identifiers which have been removed from the graph will also be
            returned.

        """
        identifiers = []

        for node in self.nodes():
            qualified_name = node.package.definition_identifier
            name = qualified_name.split(wiz.symbol.NAMESPACE_SEPARATOR, 1)[-1]
            if requirement.name not in [qualified_name, name]:
                continue

            # Node is matching if package has no version.
            if node.package.version is None:
                identifiers.append(node.package.qualified_identifier)

            # Node is matching if requirement contains package version.
            elif requirement.specifier.contains(node.package.version):
                identifiers.append(node.package.qualified_identifier)

        return identifiers

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

    def conflicting_identifiers(self):
        """Return conflicting nodes identifiers.

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

    def error_identifiers(self):
        """Return list of existing node identifiers which encapsulate an error.
        """
        return [
            identifier for identifier in self._error_mapping.keys()
            if identifier == self.ROOT or self.exists(identifier)
        ]

    def errors(self, identifier):
        """Return list of exceptions raised for node *identifier*."""
        return self._error_mapping.get(identifier)

    def update_from_requirements(self, requirements, parent_identifier):
        """Update graph from *requirements*.

        *requirements* should be a list of
        class:`packaging.requirements.Requirement` instances ordered from the
        most important to the least important.

        *parent_identifier* should indicate a parent node identifier.

        One or several :class:`~wiz.package.Package` instances will be
        extracted from  *requirements* and :class:`Node` instances will be added
        to graph accordingly. The process will be repeated recursively for
        dependent requirements from newly created packages.

        Package's requirement are traversed with a `Breadth-first search
        <https://en.wikipedia.org/wiki/Breadth-first_search>`_ algorithm so that
        potential errors are raised for top-level packages first.

        Conditions will be recorded as :class:`StoredNode` instances.
        Corresponding packages will be added to the graph only if at least one
        package with the same definition identifier has previously been added
        to the graph.

        """
        queue = _queue.Queue()

        wiz.history.record_action(
            wiz.symbol.GRAPH_UPDATE_ACTION,
            graph=self, requirements=requirements,
        )

        # Record namespaces from all requirement names.
        self._update_namespace_count(requirements)

        # Fill up queue from requirements and update the graph accordingly.
        for index, requirement in enumerate(requirements):
            queue.put({
                "requirement": requirement,
                "parent_identifier": parent_identifier,
                "weight": index + 1
            })

        self._update(queue)

    def update_from_package(
        self, package, requirement, parent_identifier=None, weight=1
    ):
        """Update graph from *package*.

        *package* should be a class:`~wiz.package.Package` instance.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement` which led to the *package*
        extraction.

        *parent_identifier* can indicate a parent node identifier. Default is
        None, which means that *package* will not be linked to any parent.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. The lesser this number, the higher is
        the importance of the link. Default is 1.

        .. note::

            *weight* is irrelevant if no *parent_identifier* is given.

        """
        queue = _queue.Queue()

        wiz.history.record_action(
            wiz.symbol.GRAPH_UPDATE_ACTION,
            graph=self, requirements=[requirement],
        )

        # Record namespaces from all requirement names.
        self._update_namespace_count([requirement])

        # Add package to queue to start updating.
        queue.put({
            "requirement": requirement,
            "package": package,
            "parent_identifier": parent_identifier,
            "weight": weight
        })

        self._update(queue)

    def _update(self, queue):
        """Update graph and fetch stored nodes from data contained in *queue*.

        *queue* should be a :class:`Queue` instance.

        """
        self._update_from_queue(queue)

        # Update graph with conditioned nodes stored if necessary.
        stored_nodes = self._fetch_required_stored_nodes()

        while len(stored_nodes) > 0:
            for stored_node in stored_nodes:
                queue.put({
                    "requirement": stored_node.requirement,
                    "package": stored_node.package,
                    "parent_identifier": stored_node.parent_identifier,
                    "weight": stored_node.weight
                })

            self._update_from_queue(queue)

            # Check if new stored nodes need to be added to graph.
            stored_nodes = self._fetch_required_stored_nodes()

    def _fetch_required_stored_nodes(self):
        """Return :class:`StoredNode` instances which should be added to graph.

        A :class:`StoredNode` instance has been created for each package which
        has one or several conditions.

        """
        stored_nodes = []

        for stored_node in self._conditioned_nodes:
            # Prevent adding stored nodes twice into the graph
            if self.exists(stored_node.identifier):
                continue

            try:
                packages = (
                    wiz.package.extract(
                        condition, self._resolver.definition_mapping
                    ) for condition in stored_node.package.conditions
                )

                # Require all package identifiers to be in the node mapping.
                identifiers = [
                    package.qualified_identifier
                    for package in itertools.chain(*packages)
                ]

            except wiz.exception.WizError:
                # Do not raise if the condition request is incorrect.
                continue

            if all(self.exists(_id) for _id in identifiers):
                self._logger.debug(
                    "Package '{}' fulfills conditions [{}]".format(
                        stored_node.identifier,
                        ", ".join(
                            str(req) for req in stored_node.package.conditions
                        )
                    )
                )
                stored_nodes.append(stored_node)

        return stored_nodes

    def _update_from_queue(self, queue):
        """Recursively update graph from data contained in *queue*.

        *queue* should be a :class:`Queue` instance.

        """
        while not queue.empty():
            data = queue.get()

            if data.get("package") is None:
                self._update_from_requirement(
                    data.get("requirement"),
                    data.get("parent_identifier"),
                    queue,
                    weight=data.get("weight")
                )

            else:
                self._update_from_package(
                    data.get("package"), data.get("requirement"),
                    data.get("parent_identifier"),
                    queue,
                    weight=data.get("weight")
                )

    def _update_from_requirement(
        self, requirement, parent_identifier, queue, weight=1
    ):
        """Update graph from *requirement*.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *parent_identifier* indicate a parent node identifier.

        *queue* should be a :class:`Queue` instance that will be updated with
        all dependent requirements data.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. The lesser this number, the higher is
        the importance of the link. Default is 1.

        """
        self._logger.debug("Update from requirement: {}".format(requirement))

        # Get packages from requirement.
        try:
            packages = wiz.package.extract(
                requirement, self._resolver.definition_mapping,
                namespace_counter=self._namespace_count
            )

        except wiz.exception.WizError as error:
            self._error_mapping.setdefault(parent_identifier, [])
            self._error_mapping[parent_identifier].append(error)
            return

        # Create a node for each package if necessary.
        for package in packages:
            sanitize_requirement(requirement, package.namespace)

            self._update_from_package(
                package, requirement, parent_identifier, queue,
                weight=weight
            )

    def _update_from_package(
        self, package, requirement, parent_identifier, queue, weight=1
    ):
        """Update graph from *package*.

        *package* should be an instance of :class:`wiz.package.Package`.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *parent_identifier* indicate a parent node identifier.

        *queue* should be a :class:`Queue` instance that will be updated with
        all dependent requirements data.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. The lesser this number, the higher is
        the importance of the link. Default is 1.

        """
        identifier = package.qualified_identifier

        if not self.exists(identifier):

            # Do not add the node to the graph if conditions are unprocessed.
            if (
                len(package.conditions) > 0 and
                not package.get("conditions-processed")
            ):
                self._conditioned_nodes.append(
                    StoredNode(
                        requirement,
                        package.set("conditions-processed", True),
                        parent_identifier=parent_identifier,
                        weight=weight
                    )
                )
                return

            self._create_node_from_package(package)

            # Update queue with dependent requirement.
            for index, _requirement in enumerate(package.requirements):
                queue.put({
                    "requirement": _requirement,
                    "parent_identifier": identifier,
                    "weight": index + 1
                })

        else:
            # Update variant mapping if necessary
            self._update_variant_mapping(identifier)

        node = self._node_mapping[identifier]

        if parent_identifier is not None:
            node.add_parent(parent_identifier)

            # Create links with requirement and weight.
            self.create_link(
                node.identifier,
                parent_identifier,
                requirement,
                weight=weight
            )

    def _create_node_from_package(self, package):
        """Create node in graph from *package*.

        *package* should be a :class:`~wiz.package.Package` instance.

        """
        identifier = package.qualified_identifier

        self._logger.debug("Adding package: {}".format(identifier))
        self._node_mapping[identifier] = Node(package)

        # Record node identifiers per package to identify conflicts.
        _definition_id = package.definition_identifier
        self._identifiers_per_definition.setdefault(_definition_id, set())
        self._identifiers_per_definition[_definition_id].add(identifier)

        # Record variant per unique key identifier if necessary.
        self._update_variant_mapping(identifier)

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODE_CREATION_ACTION, graph=self, node=identifier
        )

    def _update_variant_mapping(self, identifier):
        """Update variant mapping according to node *identifier*.
        """
        node = self._node_mapping[identifier]
        if node.variant_name is None:
            return

        # TODO: Shouldn't it be a set?
        self._variants_per_definition.setdefault(node.definition, [])
        self._variants_per_definition[node.definition].append(identifier)

    def _update_namespace_count(self, requirements):
        """Record namespace occurrences from *requirements*.

        Requirement names are used to find out all available namespaces.

        *requirements* should be a list of
        class:`packaging.requirements.Requirement` instances.

        """
        mapping = self._resolver.definition_mapping.get("__namespace__", {})

        namespaces = []

        for requirement in requirements:
            namespaces += mapping.get(requirement.name, [])

        self._namespace_count.update(namespaces)

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

        .. note::

            If a link already exists between *identifier* and
            *parent_identifier*, it will be overwritten only if the new weight
            is lower than the current one. This way, the priority of the node
            can raise, but never decrease.

        """
        self._link_mapping.setdefault(parent_identifier, {})

        if identifier in self._link_mapping[parent_identifier].keys():
            _weight = (
                self._link_mapping[parent_identifier][identifier]["weight"]
            )

            # Skip if a link is already set between these two nodes with
            # a lower weight:
            if weight > _weight:
                return

        self._logger.debug(
            "Add dependency link from '{parent}' to '{child}' "
            "[weight: {weight}]".format(
                parent=parent_identifier,
                child=identifier,
                weight=weight
            )
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
            :class:`~wiz.package.Package` instance qualified identifier.

        """
        return self._package.qualified_identifier

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
        """Add *identifier* as parent to the node."""
        self._parent_identifiers.add(identifier)

    def to_dict(self):
        """Return corresponding dictionary."""
        return {
            "package": self._package.to_dict(serialize_content=True),
            "parents": list(self._parent_identifiers)
        }


class StoredNode(object):
    """Representation of a node mapping within the :class:`Graph`.

    It encapsulates one :class:`packaging.requirements.Requirement` instance
    and corresponding :class:`wiz.package.Package` instance retrieved with
    its parent package identifier and a weight number.

    A StoredNode instance is used when a package request cannot be immediately
    added to the graph.

    Examples:

    * When a package contains conditions, a StoredNode instance is created for
      this package request until the validation can be validated. If the
      conditions are not validated, the package will not be added to the graph.

    """

    def __init__(self, requirement, package, parent_identifier, weight=1):
        """Initialize StoredNode.

        *requirement* should be an instance of
        :class:`packaging.requirements.Requirement`.

        *package* should be an instance of :class:`wiz.package.Package`.

        *parent_identifier* indicate a parent node identifier.

        *weight* is a number which indicate the importance of the dependency
        link from the node to its parent. Default is 1.

        """
        self._requirement = requirement
        self._package = package
        self._parent_identifier = parent_identifier
        self._weight = weight

    @property
    def identifier(self):
        """Return identifier of the stored node.

        .. note::

            The node identifier is the same as the embedded
            :class:`~wiz.package.Package` instance qualified identifier.

        """
        return self._package.qualified_identifier

    @property
    def requirement(self):
        """Return :class:`packaging.requirements.Requirement` instance."""
        return self._requirement

    @property
    def package(self):
        """Return :class:`wiz.package.Package` instance."""
        return self._package

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
            "package": self.package.to_dict(serialize_content=True),
            "parent_identifier": self._parent_identifier,
            "weight": self._weight
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


class Timeout(object):
    """Handle a time out on :class:`Graph` methods.

    Raise :exc:`wiz.exception.GraphResolutionError` when the time limit is
    reached.

    .. warning::

        It does not work on Windows operating system as it uses
        :func:`signal.alarm` to raise the exception.

    """
    def __init__(self, seconds):
        self._time_limit = seconds

    def __enter__(self):
        signal.signal(signal.SIGALRM, self._raises_exception)
        signal.setitimer(signal.ITIMER_REAL, self._time_limit)

    def __exit__(self, _type, value, traceback):
        signal.alarm(0)

    def _raises_exception(self, signum, frame):
        raise wiz.exception.GraphResolutionError(
            "Timeout reached. Graph resolution took too long."
        )

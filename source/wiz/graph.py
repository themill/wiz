# :coding: utf-8

import copy
import itertools
import uuid
import signal
import collections
from heapq import heapify, heappush, heappop
try:
    import queue as _queue
except ImportError:
    import Queue as _queue

import wiz.logging
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
        >>> graph.variant_groups()

        [
            ["foo[V3]", "foo[V2]", "foo[V1]"],
            ["bar[V2]", "bar[V1]"],
            ["baz[V4]", "baz[V3]", "baz[V2]", "baz[V1]"],
        ]

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
        self._logger = wiz.logging.Logger(__name__ + ".Resolver")

        # All available definitions.
        self._definition_mapping = definition_mapping

        # Set of node identifiers with variants which required graph division.
        self._variant_identifiers = set()

        # Record mapping indicating the shortest possible distance of each node
        # identifier from the root level of the graph with corresponding
        # parent node identifier.
        self._distance_mapping = None

        # Iterator which yield the next graph to resolve with a list of
        # conflicting variant node identifiers to remove before instantiation.
        self._iterator = iter([])

        # Time limit for the resolution process.
        self._timeout = timeout

        # Record node identifiers with error to prevent it being used in more
        # than one combination.
        self._node_errors = set()

        # Record mapping of all conflicting identifiers found during the
        # graph resolution failed attempts.
        self._conflicts_mapping = {}

        # Record all requirement conflict tuples which contains the
        # corresponding graph and a set of conflicting identifiers. A Deque is
        # used as it is a FIFO queue.
        self._conflicts = collections.deque()

    @property
    def definition_mapping(self):
        """Return mapping of all available definitions."""
        return self._definition_mapping

    def compute_packages(self, requirements):
        """Resolve requirements graphs and return list of packages.

        *requirements* should be a list of
        :class:`packaging.requirements.Requirement` instances.

        Raise :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
        resolved in time.

        """
        with Timeout(self._timeout):
            return self._compute_packages(requirements)

    def _compute_packages(self, requirements):
        """Resolve requirements graphs and return list of packages.

        *requirements* should be a list of
        :class:`packaging.requirements.Requirement` instances.

        """
        graph = Graph(self)

        wiz.history.record_action(
            wiz.symbol.GRAPH_CREATION_ACTION,
            graph=graph, requirements=requirements
        )

        # Update the graph.
        graph.update_from_requirements(requirements, graph.ROOT)

        self._initiate_iterator(graph)

        # Store latest exception to raise if necessary.
        latest_error = None

        # Record the number of failed resolution attempts.
        nb_failures = 0

        while True:
            graph, nodes_to_remove = self._fetch_next_combination()
            if graph is None:
                latest_error.message = (
                    "Failed to resolve graph at combination #{}:\n\n"
                    "{}".format(nb_failures, latest_error.message)
                )
                raise latest_error

            try:
                # Compute new graph.
                graph = self._compute_combination(graph, nodes_to_remove)

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

                # Extract existing node errors in the graph.
                self._node_errors.update(graph.error_identifiers())

                # Extract conflicting identifiers and requirements if possible.
                self._update_conflicts(error)

                self._logger.debug("Failed to resolve graph: {}".format(error))
                latest_error = error
                nb_failures += 1

    def _update_conflicts(self, exception):
        """Extract and record conflicts from *exception* if possible.

        Conflicts are only recorded in :exc:`wiz.exception.GraphResolutionError`
        exceptions.

        """
        if not isinstance(exception, wiz.exception.GraphResolutionError):
            return

        for mapping in exception.conflicts:
            graph = mapping["graph"]
            identifiers = mapping["identifiers"]
            conflicts = mapping["conflicts"]

            self._conflicts.append((graph, identifiers))

            for identifier in identifiers:
                for conflict in conflicts:
                    self._conflicts_mapping.setdefault(identifier, {})
                    self._conflicts_mapping[identifier][conflict] = mapping

    def _initiate_iterator(self, graph):
        """Initialize iterator with a *graph*.

        *graph* must be an instance of :class:`Graph`.

        """
        self._logger.debug("Initiate iterator from graph")

        # Reset the iterator.
        self._iterator = iter([])

        # Initialize combinations or simply add graph to iterator.
        if not self._extract_combinations(graph):
            self._iterator = iter([(graph, [])])

    def _extract_combinations(self, graph):
        """Extract possible combinations from variant conflicts in *graph*.

        Return a boolean value indicating whether combination generator has been
        added to the iterator.

        *graph* must be an instance of :class:`Graph`.

        """
        variant_groups = graph.variant_groups()
        if not variant_groups:
            self._logger.debug(
                "No package variants are conflicting in the graph."
            )
            return False

        # Record node identifiers from all groups to prevent dividing the graph
        # twice with the same node.
        for group in variant_groups:
            for identifier in group:
                self._variant_identifiers.add(identifier)

        distance_mapping, _ = self._fetch_distance_mapping(graph)

        # Order the variant groups in ascending order of distance from the root
        # level of the graph.
        variant_groups = sorted(
            variant_groups,
            key=lambda _group: min([
                distance_mapping[_id].get("distance") for _id in _group
                if distance_mapping[_id].get("distance") is not None
            ]),
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

    def _fetch_next_combination(self):
        """Return next graph and nodes to remove from the combination iterator.

        A tuple will be returned with the next :class:`Graph` instance and a
        list of nodes to remove from it.

        If the combination iterator is empty, the graph will be returned as
        None and the node removal list will be empty.

        """
        # Reset the distance mapping for new graph.
        self._distance_mapping = None

        while True:
            try:
                graph, nodes_to_remove = next(self._iterator)

                # To prevent mutating any copy of the instance.
                return copy.deepcopy(graph), nodes_to_remove

            except StopIteration:
                self._logger.debug(
                    "No more combination in"
                )

                # If iterator is empty, check the requirement conflicts to find
                # out if a new graph could be computed with different versions.
                if not self._reinitiate_from_conflicts():
                    self._logger.debug(
                        "Impossible to reinitiate the iterator from previous "
                        "requirement conflicts"
                    )

                    return None, []

    def _reinitiate_from_conflicts(self):
        """Re-initialize iterator from recorded requirement conflicts.

        After exhausting all graph combinations, the requirement conflicts
        previously recorded are using to create another graph with different
        node versions.

        For instance, if a conflict has been recording for the following nodes::

            * foo==3.2.1
            * bar==1.1.1

        A new graph will be created with other versions for these two node if
        possible.

        """
        while True:
            try:
                graph, identifiers = self._conflicts.popleft()
            except IndexError:
                return False

            # To prevent mutating any copy of the instance.
            _graph = copy.deepcopy(graph)

            # Iterator can be initialized only if all identifiers can be
            # replaced with lower version.
            if not self._replace_versions_in_graph(_graph, identifiers):
                continue

            # Reset the iterator.
            self._initiate_iterator(_graph)

            return True

    def _replace_versions_in_graph(self, graph, identifiers):
        """Replace all node *identifiers* in *graph* with different versions.

        Return True if all node *identifiers* were replaced with different
        versions. Return False if at least one node cannot be replaced.

        *graph* must be an instance of :class:`Graph`.

        *identifiers* should be valid node identifiers.

        """
        # Record replacement mapping for debugging purposes.
        replacement = {}

        for identifier in identifiers:
            self._logger.debug(
                "Attempt to fetch another version for conflicting package "
                "'{}'".format(identifier)
            )
            node = graph.node(identifier)

            # If the node cannot be fetched or does not have a version, it is
            # impossible to replace it with another version.
            if node is None or node.package.version == wiz.symbol.UNKNOWN_VALUE:
                self._logger.debug(
                    "Impossible to fetch another version for conflicting "
                    "package '{}'".format(identifier)
                )
                return False

            # Extract combined requirement to node and modify it to exclude
            # current package version.
            requirement = combined_requirements(graph, [node])
            exclusion_requirement = wiz.utility.get_requirement(
                "{} != {}".format(requirement.name, node.package.version)
            )
            requirement.specifier &= exclusion_requirement.specifier

            try:
                packages = wiz.package.extract(
                    requirement, self._definition_mapping
                )
            except wiz.exception.RequestNotFound:
                self._logger.debug(
                    "Impossible to fetch another version for conflicting "
                    "package '{}' with following "
                    "request: '{}'".format(identifier, requirement)
                )
                return False

            # Remove conflicting node from graph.
            graph.remove_node(identifier)

            # Add new node version to graph.
            for package in packages:
                graph.update_from_package(package, requirement)

            # Relink nodes.
            relink_parents(graph, node)

            # Record resulting replacement
            replacement[identifier] = [p.qualified_identifier for p in packages]

        self._logger.debug(
            "Create new graph with new nodes:\n"
            "{}".format(
                "\n".join([
                    "  * {} -> {}".format(identifier, identifiers)
                    for identifier, identifiers in replacement.items()
                ])
            )
        )

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODES_REPLACEMENT_ACTION,
            graph=graph, mapping=replacement
        )

        return True

    def _compute_combination(self, graph, nodes_to_remove):
        """Compute and return processed *graph* from combination.

        *graph* must be an instance of :class:`Graph`.

        *nodes_to_remove* should be a list of node identifiers that should be
        removed from the graph as part of this combination.

        Raise :exc:`wiz.exception.GraphResolutionError` if the parent of nodes
        removed cannot be re-linked to any existing node in the graph.

        """
        self._logger.debug(
            "Generate graph without following nodes: {!r}".format(
                nodes_to_remove
            )
        )

        wiz.history.record_action(
            wiz.symbol.GRAPH_COMBINATION_EXTRACTION_ACTION,
            graph=graph, nodes_to_remove=nodes_to_remove
        )

        removed_nodes = []

        for identifier in nodes_to_remove:
            node = graph.node(identifier)
            graph.remove_node(identifier)
            removed_nodes.append(node)

        for node in removed_nodes:
            relink_parents(graph, node)

        # Prune unreachable and invalid nodes if necessary.
        if len(removed_nodes) > 0:
            self._prune_graph(graph)

        # Raise if combination contains known error or conflicts.
        self._check_errors_in_combination(graph)
        self._check_conflicts_in_combination(graph)

        return graph

    def _check_errors_in_combination(self, graph):
        """Check whether known errors are found in *graph* combination.

        If so, a :exc:`wiz.exception.GraphResolutionError` is raised and the
        combination is skipped.

        """
        all_identifiers = [graph.ROOT] + graph.identifiers()

        # Check nodes with remaining errors.
        identifiers = self._node_errors.intersection(all_identifiers)

        if len(self._node_errors.intersection(all_identifiers)) > 0:
            _raise_node_errors(graph, identifiers)

    def _check_conflicts_in_combination(self, graph):
        """Check whether known conflicts are found in *graph* combination.

        If so, a :exc:`wiz.exception.GraphResolutionError` is raised and the
        combination is skipped.

        """
        all_identifiers = [graph.ROOT] + graph.identifiers()

        for identifier in all_identifiers:
            mapping = self._conflicts_mapping.get(identifier, {})
            conflicts = set(mapping.keys())

            # Check nodes with remaining conflicts.
            identifiers = conflicts.intersection(all_identifiers)

            if len(identifiers) > 0:
                conflict_mappings = (
                    (
                        self._conflicts_mapping[identifier][_id],
                        self._conflicts_mapping[_id][identifier]
                    )
                    for _id in identifiers
                )

                _raise_node_conflicts(
                    itertools.chain(*conflict_mappings),
                    record_conflicts=False
                )

    def _resolve_conflicts(self, graph):
        """Attempt to resolve all conflicts in *graph*.

        *graph* must be an instance of :class:`Graph`.

        Raise :exc:`wiz.exception.GraphResolutionError` if several node
        requirements are incompatible.

        Raise :exc:`wiz.exception.GraphResolutionError` if new package
        versions added to the graph during the resolution process lead to
        a division of the graph.

        Raise :exc:`wiz.exception.GraphResolutionError` if the parent of nodes
        removed cannot be re-linked to any existing node in the graph.

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
            # If no nodes are left in the queue, exit the loop. The graph
            # is officially resolved. Hooray!
            if not conflicts:
                return

            # Sort conflicting nodes by distances.
            distance_mapping, updated = self._fetch_distance_mapping(graph)

            if updated:
                conflicts = updated_by_distance(conflicts, distance_mapping)

            # Pick up the furthest conflicting node identifier so that nearest
            # node have priorities.
            identifier = conflicts.pop()
            node = graph.node(identifier)

            # If node has already been removed from graph, ignore.
            if node is None:
                continue

            # Identify nodes conflicting with this node. Return if none are
            # found.
            conflicting_nodes = extract_conflicting_nodes(graph, node)
            if len(conflicting_nodes) == 0:
                continue

            # Compute valid node identifier from combined requirements.
            requirement = combined_requirements(
                graph, [node] + conflicting_nodes
            )

            # Query packages from combined requirement.
            packages = self._extract_packages(
                requirement, graph, [node] + conflicting_nodes, conflicts
            )
            if packages is None:
                continue

            # If current node is not part of the extracted packages, it will be
            # removed from the graph.
            if not any(
                node.identifier == package.qualified_identifier
                for package in packages
            ):
                self._logger.debug("Remove '{}'".format(node.identifier))
                graph.remove_node(node.identifier)

                # The graph changed in a way that can affect the distances of
                # other nodes, so the distance mapping cached is discarded.
                self._distance_mapping = None

                # Update the graph if necessary
                updated = self._add_packages_to_graph(
                    graph, packages, requirement, conflicting_nodes
                )

                # Relink node parents to package identifiers. It needs to be
                # done before possible combination extraction otherwise newly
                # added nodes will remained parent-less and will be discarded.
                relink_parents(graph, node, requirement)

                # Update conflict list if necessary.
                if updated:
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

            self._prune_graph(graph)

    def _extract_packages(
        self, requirement, graph, nodes, conflicting_identifiers
    ):
        """Return packages extracted from combined *requirement*.

        If no packages could be extracted, *nodes* parent identifiers are
        extracted from *graph* to ensure that they are not listed as
        *conflicts*. If this is the case, the error is discarded and None is
        returned. Otherwise, :exc:`wiz.exception.GraphResolutionError` is
        raised.

        *requirement* must be a :class:`packaging.requirements.Requirement`
        instance.

        *graph* must be an instance of :class:`Graph`.

        *nodes* must be a list of :class:`Node` instances.

        *conflicting_identifiers* must be a list of node identifiers conflicting
        in *graph*.

        """
        try:
            packages = wiz.package.extract(
                requirement, self._definition_mapping
            )
        except wiz.exception.RequestNotFound:
            conflict_mappings = extract_conflicting_requirements(graph, nodes)
            parents = set(
                identifier
                for mapping in conflict_mappings
                for identifier in mapping["identifiers"]
            )

            # Discard conflicting nodes if parents are themselves
            # conflicting.
            if len(parents.intersection(conflicting_identifiers)) > 0:
                return

            _raise_node_conflicts(conflict_mappings)

        else:
            return packages

    def _add_packages_to_graph(
        self, graph, packages, requirement, conflicting_nodes
    ):
        """Add extracted *packages* not represented as conflict to *graph*.

        A package is not added to the *graph* if:

        * It is already represented as a conflicted nodes.
        * It has already led to a graph division.

        Return whether the graph has been updated with at least one package.

        *graph* must be an instance of :class:`Graph`.

        *packages* must be a list of :class:`~wiz.package.Package` instances
        that has been extracted from *requirement*. The list contains more than
        one package only if variants are detected.

        *requirement* must be the :class:`packaging.requirements.Requirement`
        which led to the package extraction. It is a :func:`combined requirement
        <wiz.graph.combined_requirements>` from all requirements which extracted
        packages embedded in *conflicting_nodes*.

        *conflicting_nodes* should be a list of :class:`Node` instances
        representing conflicting version for the same definition identifier as
        *packages* within the *graph*.

        """
        identifiers = set([p.qualified_identifier for p in packages])

        # Filter out identifiers already set as conflict.
        identifiers.difference_update([n.identifier for n in conflicting_nodes])

        # Filter out identifiers which already led to graph division.
        identifiers.difference_update(self._variant_identifiers)

        if len(identifiers):
            self._logger.debug(
                "Add to graph: {}".format(", ".join(identifiers))
            )

            for package in packages:
                graph.update_from_package(package, requirement)

            return True

        return False

    def _prune_graph(self, graph):
        """Remove unreachable and invalid nodes from *graph*.

        The pruning process is done as follow:

        1. If the graph distance mapping has been updated, all unreachable nodes
           will be removed. Otherwise the method will return.

        2. If nodes have been removed, another pass through all nodes in the
           graph ensure that all invalid nodes are removed (e.g. when conditions
           are no longer fulfilled).

        3. Step 1 and 2 are repeated until the distance mapping is not updated.

        *graph* must be an instance of :class:`Graph`.

        """
        while True:
            distance_mapping, updated = self._fetch_distance_mapping(graph)
            if not updated:
                return

            # Remove all unreachable nodes if the graph has been updated. Reset
            # the distance mapping if nodes have been removed.
            if trim_unreachable_from_graph(graph, distance_mapping):
                self._distance_mapping = None

            # Fetch updated distance mapping or return now.
            distance_mapping, updated = self._fetch_distance_mapping(graph)
            if not updated:
                return

            # Search and trim invalid nodes from graph if conditions are no
            # longer fulfilled. If so reset the distance mapping.
            while trim_invalid_from_graph(graph, distance_mapping):
                self._distance_mapping = None


def _raise_node_errors(graph, identifiers):
    """Raise exception for node *identifier* in *graph* containing errors.

    Raise :exc:`wiz.exception.GraphResolutionError`.

    *graph* must be an instance of :class:`Graph`.

    *identifiers* should be valid node identifiers.

    """
    raise wiz.exception.GraphResolutionError(
        "The dependency graph could not be resolved due to the following "
        "error(s):\n"
        "{}\n".format(
            "\n".join([
                "  * {}: {}".format(identifier, exception)
                for identifier in identifiers
                for exception in graph.errors(identifier)
            ])
        )
    )


def _raise_node_conflicts(mappings, record_conflicts=True):
    """Raise exception for list of conflict *mappings*.

    Raise :exc:`wiz.exception.GraphResolutionError`.

    *mappings* should be a list of conflict mappings in the form of::

        [
            {
                "requirement": Requirement("foo >=0.1.0, <1"),
                "identifiers": {"bar", "bim"},
                "conflicts": {"baz"},
                "graph": Graph()
            },
            {
                "requirement": Requirement("foo >2"),
                "identifiers": {"baz"},
                "conflicts": {"bar", "bim"},
                "graph": Graph()
            }
        ]

    *record_conflicts* indicate whether conflict *mappings* should be recorded
    within the exception raised.

    """
    def _format(mapping):
        """Display conflicting *mapping*."""
        identifiers = list(mapping["identifiers"])[:3]
        if len(mapping["identifiers"]) > 3:
            others = len(mapping["identifiers"]) - 3
            identifiers += ["+{} packages...".format(others)]

        return "  * {requirement} \t[{identifiers}]".format(
            requirement=mapping["requirement"],
            identifiers=", ".join(identifiers)
        )

    raise wiz.exception.GraphResolutionError(
        "The dependency graph could not be resolved due to the "
        "following requirement conflicts:\n"
        "{}\n".format("\n".join([_format(m) for m in mappings])),
        conflicts=mappings if record_conflicts else []
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
    logger = wiz.logging.Logger(__name__ + ".compute_distance_mapping")
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
            variant_name = node.package.variant_name
            variant_mapping.setdefault(variant_name, [])
            variant_mapping[variant_name].append(node_identifier)
            variant_mapping[variant_name].sort(
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

    Return boolean indicating if nodes have been removed.

    If a node within the *graph* does not have a distance, it means that it
    cannot be reached from the :attr:`root <Graph.ROOT>` level of the *graph*.
    It will then be lazily removed from the graph (the links are preserved to
    save on computing time).

    *graph* must be an instance of :class:`Graph`.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    *graph* with its corresponding parent node identifier.

    """
    logger = wiz.logging.Logger(__name__ + ".trim_unreachable_from_graph")

    nodes_removed = False

    for node in graph.nodes():
        if distance_mapping[node.identifier].get("distance") is None:
            logger.debug("Remove '{}'".format(node.identifier))
            graph.remove_node(node.identifier)
            nodes_removed = True

    return nodes_removed


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
    logger = wiz.logging.Logger(__name__ + ".trim_invalid_from_graph")

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
        _identifiers,
        key=lambda _id: (-distance_mapping[_id]["distance"], _id),
        reverse=True
    )


def extract_conflicting_nodes(graph, node):
    """Return all nodes from *graph* conflicting with *node*.

    A node from the *graph* is in conflict with the node *identifier* when
    its definition identifier is identical.

    *graph* must be an instance of :class:`Graph`.

    *node* should be a :class:`Node` instance.

    """
    nodes = (graph.node(_id) for _id in graph.conflicting_identifiers())

    # Extract definition identifier
    definition_identifier = node.definition.qualified_identifier

    return [
        _node for _node in nodes
        if _node.definition.qualified_identifier == definition_identifier
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


def extract_conflicting_requirements(graph, nodes):
    """Return list of conflicting requirement mappings.

    The list returned should be in the form of::

        [
            {
                "requirement": Requirement("foo >=0.1.0, <1"),
                "identifiers": {"bar", "bim"},
                "conflicts": {"baz"},
                "graph": Graph()
            },
            {
                "requirement": Requirement("foo >2"),
                "identifiers": {"baz"},
                "conflicts": {"bar", "bim"},
                "graph": Graph()
            }
        ]

    A requirement is conflicting when it is not overlapping with at least one
    other requirement from existing parents of *nodes*. The conflict list
    is sorted based on the number of times a requirement is conflicting.

    *graph* must be an instance of :class:`Graph`.

    *nodes* should be a list of :class:`Node` instances which belong to the
    same definition identifier.

    """
    # Ensure that definition requirement is the same for all nodes.
    definitions = set(node.definition.qualified_identifier for node in nodes)
    if len(definitions) > 1:
        raise wiz.exception.GraphResolutionError(
            "All nodes should have the same definition identifier when "
            "attempting to extract conflicting requirements from parent "
            "nodes [{}]".format(", ".join(sorted(definitions)))
        )

    # Identify all parent node identifier per requirement.
    mapping1 = {}

    for node in nodes:
        for parent_identifier in node.parent_identifiers:
            # Filter out non existing nodes from incoming.
            if (
                parent_identifier != graph.ROOT and
                not graph.exists(parent_identifier)
            ):
                continue

            identifier = node.identifier
            requirement = graph.link_requirement(identifier, parent_identifier)

            mapping1.setdefault(requirement, set([]))
            mapping1[requirement].add(parent_identifier)

    # Identify all conflicting requirements.
    mapping2 = {}

    for tuple1, tuple2 in (
        itertools.combinations(mapping1.items(), 2)
    ):
        requirement1, requirement2 = tuple1[0], tuple2[0]
        if not wiz.utility.is_overlapping(requirement1, requirement2):
            mapping2.setdefault(requirement1, set([]))
            mapping2.setdefault(requirement2, set([]))
            mapping2[requirement1].add(requirement2)
            mapping2[requirement2].add(requirement1)

    # Create conflict mapping list.
    conflicts = []

    for requirement, conflicting_requirements in sorted(
        mapping2.items(), key=lambda v: (len(v[1]), str(v[0])), reverse=True
    ):
        conflicts.append({
            "graph": graph,
            "requirement": requirement,
            "identifiers": mapping1[requirement],
            "conflicts": set(itertools.chain(
                *[mapping1[r] for r in conflicting_requirements]
            ))
        })

    return conflicts


def relink_parents(graph, node, requirement=None):
    """Relink *node*'s parents to *identifiers*.

    When creating the new links, the same weight connecting the *node* to its
    parents is being used. *requirement* will be used for each new link if
    given, otherwise the same requirement connecting the *node* to its parents
    is being used

    *graph* must be an instance of :class:`Graph`.

    *node* should be a :class:`Node` instance.

    *requirement* could be a :class:`packaging.requirements.Requirement`
    instance which should be used for .

    Raise :exc:`wiz.exception.GraphResolutionError` if one *node* parent cannot
    be re-linked to any existing node in the graph.

    """
    nodes = None

    if requirement is not None:
        nodes = [
            graph.node(identifier) for identifier in graph.find(requirement)
            if graph.exists(identifier)
        ]

    for parent_identifier in node.parent_identifiers:
        if (
            not graph.exists(parent_identifier) and
            not parent_identifier == graph.ROOT
        ):
            continue

        weight = graph.link_weight(node.identifier, parent_identifier)
        _requirement = requirement or graph.link_requirement(
            node.identifier, parent_identifier
        )

        _nodes = nodes or [
            graph.node(identifier) for identifier in graph.find(_requirement)
            if graph.exists(identifier)
        ]

        if not len(_nodes):
            raise wiz.exception.GraphResolutionError(
                "'{}' can not be linked to any existing node in graph with "
                "requirement '{}'".format(
                    parent_identifier, _requirement
                )
            )

        for _node in _nodes:
            _node.add_parent(parent_identifier)

            graph.create_link(
                _node.identifier,
                parent_identifier,
                _requirement,
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

    A :exc:`wiz.exception.GraphResolutionError` is raised if an error attached
    to the :attr:`root <Graph.ROOT>` level or any reachable node is found.

    """
    logger = wiz.logging.Logger(__name__ + ".validate")

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
            "The dependency graph does not contain any valid packages."
        )

    # Pick up nearest node identifier which contains errors.
    identifier = identifiers[0]

    _raise_node_errors(graph, [identifier])


def extract_ordered_packages(graph, distance_mapping):
    """Return sorted list of packages from *graph*.

    Best matching :class:`~wiz.package.Package` instances are
    extracted from each node instance and added to the list.

    *distance_mapping* is a mapping indicating the shortest possible distance
    of each node identifier from the :attr:`root <Graph.ROOT>` level of the
    graph with its corresponding parent node identifier.

    """
    logger = wiz.logging.Logger(__name__ + ".extract_ordered_packages")

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
        self._logger = wiz.logging.Logger(__name__ + ".Graph")
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
        self._namespace_count = collections.Counter()

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

    def identifiers(self):
        """Return all node identifiers in the graph."""
        return self._node_mapping.keys()

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
            qualified_name = node.definition.qualified_identifier
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

    def variant_groups(self):
        """Return variant groups in graphs.

        A variant group list should contain at least more than one node
        identifier which belongs at least to two different variant names.

        The variant group list contains unique identifiers and is sorted
        following two criteria:

        1. By the number of occurrences of each node identifier in the graph
        2. By the version and the variant value defined in the package.

        The mapping should be in the form of::

            [
                ["foo[V2]==0.1.0", "foo[V1]==0.1.0"],
                ["bar[V2]==2.1.5", "bar[V2]==2.2.0", "bar[V1]==2.1.0"]
            ]

        """
        groups = []

        for definition_identifier in self._variants_per_definition.keys():
            nodes = [
                self._node_mapping.get(identifier) for identifier
                in self._variants_per_definition[definition_identifier]
                if self._node_mapping.get(identifier)
            ]

            variant_names = set([node.package.variant_name for node in nodes])
            if len(variant_names) <= 1:
                continue

            count = collections.Counter([node.identifier for node in nodes])
            nodes = sorted(
                set(nodes),
                key=lambda n: (
                    count[n.identifier],
                    (n.package.version, n.package.variant_name)
                ),
                reverse=True
            )
            groups.append([node.identifier for node in nodes])

        return groups

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
            graph=self, requirements=requirements
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
            graph=self, requirements=[requirement]
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
        _definition_id = package.definition.qualified_identifier
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
        if node.package.variant_name is None:
            return

        # This is not a set because the number of occurrences of each identifier
        # is used to determine its priority within the variant group.
        _definition_id = node.definition.qualified_identifier
        self._variants_per_definition.setdefault(_definition_id, [])
        self._variants_per_definition[_definition_id].append(identifier)

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

    def remove_node(self, identifier):
        """Remove node from the graph.

        .. warning::

            A lazy deletion is performed as the links are not deleted to save on
            performance.

        """
        del self._node_mapping[identifier]

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
    def identifier(self):
        """Return identifier of the node.

        .. note::

            The node identifier is the same as the embedded
            :class:`~wiz.package.Package` instance qualified identifier.

        """
        return self._package.qualified_identifier

    @property
    def definition(self):
        """Return corresponding :class:`wiz.definition.Definition` instance."""
        return self._package.definition

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

        Raise :exc:`IndexError` if the object is empty.

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
            "Timeout reached. Graph dependency resolution took too long."
        )

# :coding: utf-8

import collections
import copy
import itertools
from heapq import heapify, heappush, heappop

import six.moves

import wiz.logging
import wiz.package
import wiz.exception
import wiz.symbol
import wiz.history
from wiz.utility import Requirement


class Resolver(object):
    """Graph resolver class.

    Compute a ordered list of packages from an initial list of
    :class:`packaging.requirements.Requirement` instances::

        >>> resolver = Resolver()
        >>> resolver.compute_packages(Requirement("foo"), Requirement("bar"))

        [Package("foo"), Package("bar"), Package("bim"), Package("baz")]

    A :class:`Graph` is instantiated with dependent requirements from initial
    requirements (e.g. "foo" requires "bim" and "bim" requires "baz").

    The resolution process of the graph ensure that only one version of each
    package definition is kept. If several versions of one package definition
    are in a graph, their corresponding requirement will be analyzed to ensure
    that they are compatible.::

        - 'foo==0.5.0' is required by 'foo<1';
        - 'foo==1.0.0' is required by 'foo';
        - The version '0.5.0' is matching both requirements;
        - Requirements 'foo<1' and 'foo' are seen as compatible.

    A graph cannot be resolved if two requirements are incompatibles.

    If several variants of one package definition are in the graph, the graph
    must be divided in as many graph combinations as there are variants. If
    several conflicting variant groups are in the graph, the number of graph
    division is equal to the multiplication of each variant group size. For
    instance, 24 graph divisions would be necessary for the following example
    (3 x 2 x 4)::

        >>> graph = Graph(resolver)
        >>> graph.update_from_requirements(
        ...     Requirement("foo"), Requirement("bar"), Requirement("baz")
        ... )
        >>> graph.conflicting_variant_groups()

        [
            ["foo[V3]", "foo[V2]", "foo[V1]"],
            ["bar[V2]", "bar[V1]"],
            ["baz[V4]", "baz[V3]", "baz[V2]", "baz[V1]"],
        ]

    Each combination will be generated only if the previous one failed to return
    a solution. If all graph combinations are exhausted and no solutions are
    found, other versions of the conflicting packages will be fetched to attempt
    to resolve the graph.

    """

    def __init__(self, definition_mapping):
        """Initialize Resolver with *requirements*.

        :param definition_mapping: Mapping regrouping all available definitions
            associated with their unique identifier.

        """
        self._logger = wiz.logging.Logger(__name__ + ".Resolver")

        # All available definitions.
        self._definition_mapping = definition_mapping

        # Iterator which yield the next graph to resolve with a list of
        # conflicting variant node identifiers to remove before instantiation.
        self._iterator = iter([])

        # Record all node identifiers with conflicting variants which led to a
        # graph division.
        self._conflicting_variants = set()

        # Record all requirement conflict tuples which contains the
        # corresponding graph and a set of conflicting identifiers. A Deque is
        # used as it is a FIFO queue.
        self._conflicting_combinations = collections.deque()

    @property
    def definition_mapping(self):
        """Return mapping of all available definitions."""
        return self._definition_mapping

    @property
    def conflicting_variants(self):
        """Return set of variant identifiers used to divide graph."""
        return self._conflicting_variants

    def compute_packages(self, requirements):
        """Resolve requirements graphs and return list of packages.

        :param requirements: List of :class:`packaging.requirements.Requirement`
            instances.

        :raise: :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
            resolved in time.

        """
        graph = Graph(self)

        wiz.history.record_action(
            wiz.symbol.GRAPH_CREATION_ACTION,
            graph=graph, requirements=requirements
        )

        # Update the graph.
        graph.update_from_requirements(requirements)

        self.reset_combinations(graph)

        # Store latest exception to raise if necessary.
        latest_error = None

        # Record the number of failed resolution attempts.
        nb_failures = 0

        while True:
            combination = self.fetch_next_combination()
            if combination is None:
                latest_error.message = (
                    "Failed to resolve graph at combination #{}:\n\n"
                    "{}".format(nb_failures, latest_error.message)
                )
                raise latest_error

            try:
                combination.resolve_conflicts()
                combination.validate()

                return combination.extract_packages()

            except wiz.exception.GraphResolutionError as error:
                wiz.history.record_action(
                    wiz.symbol.GRAPH_RESOLUTION_FAILURE_ACTION,
                    graph=combination.graph, error=error
                )

                # Extract conflicting identifiers and requirements if possible.
                if isinstance(error, wiz.exception.GraphConflictsError):
                    self._conflicting_combinations.extend([
                        (combination.graph, mapping["identifiers"])
                        for mapping in error.conflicts
                    ])

                # Divide the graph into new combinations if necessary
                if isinstance(error, wiz.exception.GraphVariantsError):
                    self.extract_combinations(combination.graph)

                self._logger.debug("Failed to resolve graph: {}".format(error))
                latest_error = error
                nb_failures += 1

    def reset_combinations(self, graph):
        """Initialize iterator with a *graph*.

        :param graph: Instance of :class:`Graph`.

        """
        self._logger.debug("Initiate iterator from graph")

        # Reset the iterator.
        self._iterator = iter([])

        # Initialize combinations or simply add graph to iterator.
        if not self.extract_combinations(graph):
            self._iterator = iter([GraphCombination(graph, copy_data=False)])

    def extract_combinations(self, graph):
        variant_groups = graph.conflicting_variant_groups()
        if not variant_groups:
            self._logger.debug(
                "No package variants are conflicting in the graph."
            )
            return False

        # Record node identifiers from all groups to prevent dividing the graph
        # twice with the same node.
        self._conflicting_variants.update([
            identifier for group in variant_groups for identifier in group
        ])

        distance_mapping = compute_distance_mapping(graph)

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

    def fetch_next_combination(self):
        """Return next graph and nodes to remove from the combination iterator.

        :return: Next :class:`Graph` instance and list of nodes to remove from
            it. If the combination iterator is empty, the graph will be returned
            as None and the node removal list will be empty.

        """
        try:
            return next(self._iterator)

        except StopIteration:

            # If iterator is empty, check the requirement conflicts to find
            # out if a new graph could be computed with different versions.
            if self.fetch_new_combinations():
                return next(self._iterator)

            self._logger.debug(
                "Impossible to find new graph combinations by downgrading "
                "conflicting versions"
            )

    def fetch_new_combinations(self):
        """Re-initialize iterator from recorded requirement conflicts.

        After exhausting all graph combinations, the requirement conflicts
        previously recorded are using to create another graph with different
        node versions.

        For instance, if a conflict has been recording for the following nodes::

            * foo==3.2.1
            * bar==1.1.1

        A new graph will be created with other versions for these two nodes if
        possible.

        :return: Boolean value indicating whether iterator has been
            re-initialized.

        """
        while True:
            try:
                graph, identifiers = self._conflicting_combinations.popleft()
            except IndexError:
                return False

            # Iterator can be initialized only if all identifiers can be
            # replaced with lower version.
            if not self.downgrade_conflicting_versions(graph, identifiers):
                continue

            # Reset the iterator.
            self.reset_combinations(graph)

            return True

    def downgrade_conflicting_versions(self, graph, identifiers):
        """Replace all node *identifiers* in *graph* with different versions.

        :param graph: Instance of :class:`Graph`.

        :param identifiers: List of node identifiers.

        :return: Boolean value indicating whether all node identifiers have been
            replaced with different versions. Returned value is False if at
            least one node cannot be replaced.

        """
        replacement = {}
        operations = []

        for identifier in identifiers:
            self._logger.debug(
                "Attempt to fetch another version for conflicting package "
                "'{}'".format(identifier)
            )
            node = graph.node(identifier)

            # If the node cannot be fetched or does not have a version, it is
            # impossible to replace it with another version.
            if node is None or node.package.version == wiz.symbol.UNSET_VALUE:
                self._logger.debug(
                    "Impossible to fetch another version for conflicting "
                    "package '{}'".format(identifier)
                )
                continue

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
                continue

            # Record resulting operation tuple to process replacement.
            operations.append((node, packages, requirement))

            # Record replacement logic for debugging purposes.
            replacement[identifier] = [p.identifier for p in packages]

        # If no conflicting nodes could be replaced, give up now.
        if len(operations) == 0:
            return False

        # Step 1: Add new node versions to graph.
        for _, packages, requirement in operations:
            for package in packages:
                graph.update_from_package(package, requirement, detached=True)

        # Step 2: Remove conflicting nodes from graph.
        for node, _, _ in operations:
            graph.remove_node(node.identifier)
            graph.relink_parents(node)

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


class GraphCombination(object):

    def __init__(self, graph, nodes_to_remove=None, copy_data=True):
        self._logger = wiz.logging.Logger(__name__ + ".GraphCombination")

        wiz.history.record_action(
            wiz.symbol.GRAPH_COMBINATION_EXTRACTION_ACTION,
            combination=graph, nodes_to_remove=nodes_to_remove
        )

        # Ensure that input data is not mutated if requested.
        if copy_data:
            graph = copy.deepcopy(graph)

        # Record graph which will be used in this combination.
        self._graph = graph

        # Record mapping indicating the shortest possible distance of each node
        # identifier from the root level of the graph with corresponding
        # parent node identifier.
        self._distance_mapping = None

        # Remove node identifiers from graph if required.
        if nodes_to_remove is not None:
            self._remove_nodes(nodes_to_remove)
            self.prune_graph()

    @property
    def graph(self):
        return self._graph

    def _remove_nodes(self, identifiers):
        removed_nodes = []

        for identifier in identifiers:
            node = self._graph.node(identifier)
            self._graph.remove_node(identifier)
            removed_nodes.append(node)

        for node in removed_nodes:
            self._graph.relink_parents(node)

    def resolve_conflicts(self):
        """Attempt to resolve all conflicts in *graph*.

        :raise: :exc:`wiz.exception.GraphResolutionError` if several node
            requirements are incompatible.

        :raise: :exc:`wiz.exception.GraphResolutionError` if new package
            versions added to the graph during the resolution process lead to
            a division of the graph.

        :raise: :exc:`wiz.exception.GraphResolutionError` if the parent of nodes
            removed cannot be re-linked to any existing node in the graph.

        """
        conflicts = self._graph.conflicting()
        if not conflicts:
            self._logger.debug("No conflicts in the graph.")
            return

        self._logger.debug("Conflicts: {}".format(", ".join(conflicts)))

        wiz.history.record_action(
            wiz.symbol.GRAPH_VERSION_CONFLICTS_IDENTIFICATION_ACTION,
            graph=self._graph, conflicting=conflicts
        )

        # Keep track of conflicts dependent on other conflicts.
        circular_conflicts = set()

        # Sort conflicts per distance to ensure breath-first resolution.
        remaining_conflicts = self._update_conflict_queue(conflicts)

        while len(remaining_conflicts) > 0:
            conflict_identifier = remaining_conflicts.popleft()
            node = self._graph.node(conflict_identifier)

            # If node has already been removed from graph, ignore.
            if node is None:
                continue

            # Identify group of nodes conflicting with this node.
            conflicting_nodes = self._graph.nodes(
                definition_identifier=node.definition.qualified_identifier
            )
            if len(conflicting_nodes) == 0:
                continue

            # Compute combined requirements from all conflicting nodes.
            requirement = combined_requirements(
                self._graph, [node] + conflicting_nodes
            )

            # Query common packages from this combined requirements.
            try:
                packages = self._extract_packages(
                    requirement, [node] + conflicting_nodes
                )
            except wiz.exception.GraphConflictsError as error:
                # Push conflict at the end of the queue if it has conflicting
                # parents that should be handled first.
                if (
                    len(error.parents.intersection(remaining_conflicts))
                    and conflict_identifier not in circular_conflicts
                ):
                    circular_conflicts.add(conflict_identifier)
                    remaining_conflicts.append(conflict_identifier)
                    continue

                # Otherwise, raise error and give up on current combination.
                raise

            # If current node is not part of the extracted packages, it will be
            # removed from the graph.
            if not any(
                node.identifier == package.identifier
                for package in packages
            ):
                self._logger.debug("Remove '{}'".format(node.identifier))
                self._graph.remove_node(node.identifier)

                # Update the graph if necessary
                updated = self._add_packages_to_graph(
                    packages, requirement, conflicting_nodes
                )

                # Relink node parents to package identifiers. It needs to be
                # done before possible combination extraction otherwise newly
                # added nodes will remained parent-less and will be discarded.
                self._graph.relink_parents(node, requirement=requirement)

                # If the updated graph contains conflicting variants, the
                # relevant combination must be extracted, therefore the
                # current graph combination cannot be resolved.
                if updated and len(self._graph.conflicting_variant_groups()):
                    raise wiz.exception.GraphVariantsError()

                # Prune unnecessary nodes and reset distance mapping.
                self.prune_graph()

                # Update list of remaining conflicts if necessary.
                remaining_conflicts = self._update_conflict_queue(
                    remaining_conflicts, self._graph.conflicting(),
                    circular_conflicts=circular_conflicts
                )

    def validate(self):
        error_mapping = self._graph.errors()
        if len(error_mapping) == 0:
            self._logger.debug("No errors in the graph.")
            return

        _errors = ", ".join(sorted(error_mapping.keys()))
        self._logger.debug("Errors: {}".format(_errors))

        wiz.history.record_action(
            wiz.symbol.GRAPH_ERROR_IDENTIFICATION_ACTION,
            graph=self._graph, errors=error_mapping.keys()
        )

        raise wiz.exception.GraphInvalidNodesError(error_mapping)

    def extract_packages(self):
        distance_mapping = self._fetch_distance_mapping()

        # Remove unreachable nodes.
        nodes = (
            node for node in self._graph.nodes()
            if distance_mapping.get(node.identifier, {}).get("distance")
            is not None
        )

        def _compare(node):
            """Sort identifiers per distance and parent."""
            # TODO: Identifier should probably be used as fallback instead of
            #  parent...
            return (
                distance_mapping[node.identifier]["distance"],
                distance_mapping[node.identifier]["parent"]
            )

        # Update node order by distance.
        nodes = sorted(nodes, key=_compare, reverse=True)

        # Extract packages from nodes.
        packages = [node.package for node in nodes]

        self._logger.debug(
            "Sorted packages: {}".format(
                ", ".join([package.identifier for package in packages])
            )
        )

        wiz.history.record_action(
            wiz.symbol.GRAPH_PACKAGES_EXTRACTION_ACTION,
            graph=self._graph, packages=packages
        )

        return packages

    def _update_conflict_queue(self, *args, circular_conflicts=None):
        distance_mapping = self._fetch_distance_mapping()

        # Remove unreachable nodes from circular conflicts.
        circular_conflicts = set([
            identifier for identifier in circular_conflicts or []
            if distance_mapping.get(identifier, {}).get("distance") is not None
        ])

        # Concatenate conflict lists while ignoring unreachable nodes and
        # identifiers flagged as circular conflicts so it can be added at the
        # end of the queue.
        identifiers = (
            identifier for _identifiers in args for identifier in _identifiers
            if identifier not in circular_conflicts
            and distance_mapping.get(identifier, {}).get("distance") is not None
        )

        def _compare(identifier):
            """Sort identifiers per distance and identifier."""
            return distance_mapping[identifier]["distance"], identifier

        # Update order by distance.
        conflicts = sorted(identifiers, key=_compare, reverse=True)

        # Appends nodes flagged as circular conflicts
        conflicts.extend(sorted(circular_conflicts, key=_compare, reverse=True))

        # Initiate queue.
        return collections.deque(conflicts)

    def _fetch_distance_mapping(self, force_update=False):
        """Return distance mapping from cached attribute.

        If no distance mapping is available, a new one is generated from
        *graph*.

        :param force_update: Indicate whether a new distance mapping should be
            computed, even if one cached mapping is available.

        :return: Distance mapping.

        """
        if self._distance_mapping is None or force_update:
            self._distance_mapping = compute_distance_mapping(self._graph)

        return self._distance_mapping

    def _extract_packages(self, requirement, nodes):
        """Return packages extracted from combined *requirement*.

        If no packages could be extracted, *nodes* parent identifiers are
        extracted from *graph* to ensure that they are not listed as
        *conflicts*. If this is the case, the error is discarded and None is
        returned. Otherwise, :exc:`wiz.exception.GraphResolutionError` is
        raised.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :param nodes: List of :class:`Node` instances.

        :raise: :exc:`wiz.exception.GraphResolutionError` if no packages have
            been extracted.

        :return: List of :class:`~wiz.package.Package` instances, or None.

        """
        try:
            packages = wiz.package.extract(
                requirement, self._graph.resolver.definition_mapping
            )
        except wiz.exception.RequestNotFound:
            conflict_mappings = extract_conflicting_requirements(
                self._graph, nodes
            )

            raise wiz.exception.GraphConflictsError(conflict_mappings)

        else:
            return packages

    def _add_packages_to_graph(self, packages, requirement, conflicting_nodes):
        """Add extracted *packages* not represented as conflict to *graph*.

        A package is not added to the *graph* if:

        * It is already represented as a conflicted nodes.
        * It has already led to a graph division.

        :param packages: List of :class:`~wiz.package.Package` instances
            that has been extracted from *requirement*. The list contains more
            than one package only if variants are detected.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement` which led to the package
            extraction. It is a :func:`combined requirement
            <wiz.graph.combined_requirements>` from all requirements which
            extracted packages embedded in *conflicting_nodes*.

        :param conflicting_nodes: List of :class:`Node` instances representing
            conflicting version for the same definition identifier as *packages*
            within the *graph*.

        :return: Boolean value indicating whether the graph has been updated
            with at least one package.

        """
        # Filter out identifiers already set as conflict, and identifiers which
        # already led to graph division.
        back_list = set([node.identifier for node in conflicting_nodes])
        back_list.update(self._graph.resolver.conflicting_variants)

        # Compute new packages.
        _packages = [
            package for package in packages
            if package.identifier not in back_list
        ]

        if len(_packages):
            identifier = ", ".join([package.identifier for package in packages])
            self._logger.debug("Add to graph: {}".format(identifier))

            for package in packages:
                self._graph.update_from_package(
                    package, requirement, detached=True
                )

            return True

        return False

    def prune_graph(self):
        """Remove unreachable and invalid nodes from *graph*.

        The pruning process is done as follow:

        1. If the graph distance mapping has been updated, all unreachable nodes
           will be removed. Otherwise the method will return.

        2. If nodes have been removed, another pass through all nodes in the
           graph ensure that all invalid nodes are removed (e.g. when conditions
           are no longer fulfilled).

        3. Step 1 and 2 are repeated until the distance mapping is not updated.

        """
        while True:
            # Remove all unreachable nodes if the graph has been updated.
            if not self._trim_unreachable_nodes():
                return

            # Search and trim invalid nodes from graph if conditions are no
            # longer fulfilled. Several passes might be necessary.
            if not self._trim_unfulfilled_conditions():
                return

    def _trim_unreachable_nodes(self):
        distance_mapping = self._fetch_distance_mapping(force_update=True)

        nodes_removed = False

        for node in self._graph.nodes():
            if distance_mapping[node.identifier].get("distance") is None:
                self._logger.debug("Remove '{}'".format(node.identifier))
                self._graph.remove_node(node.identifier)
                nodes_removed = True

        return nodes_removed

    def _trim_unfulfilled_conditions(self):
        needs_update = True
        nodes_removed = []

        while needs_update:
            distance_mapping = self._fetch_distance_mapping(force_update=True)
            needs_update = False

            for stored_node in self._graph.conditioned_nodes():
                # Ignore if corresponding node has not been added to the graph.
                if not self._graph.exists(stored_node.identifier):
                    continue

                # Otherwise, check whether all conditions are still fulfilled.
                for requirement in stored_node.package.conditions:
                    identifiers = self._graph.find(requirement)

                    if len(identifiers) == 0 or any(
                        distance_mapping.get(_id, {}).get("distance") is None
                        for _id in identifiers
                    ):
                        self._logger.debug(
                            "Remove '{}' as conditions are no longer "
                            "fulfilled".format(stored_node.identifier)
                        )
                        self._graph.remove_node(stored_node.identifier)
                        nodes_removed.append(stored_node.identifier)
                        needs_update = True
                        break

        return len(nodes_removed) > 0


def compute_distance_mapping(graph):
    """Return distance mapping for each node of *graph*.

    The mapping indicates the shortest possible distance of each node
    identifier from the :attr:`root <Graph.ROOT>` level of the *graph* with
    corresponding parent node identifier.

    The distance is defined by the sum of the weights from each node to the
    :attr:`root <Graph.ROOT>` level of the *graph*.

    This is using `Dijkstra's shortest path algorithm
    <https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm>`_.

    :param graph: Instance of :class:`Graph`.

    :return: Distance mapping.

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

    Each list of variant groups contains node identifiers added to the *graph*
    in the order of importance which share the same definition identifier and
    variant identifier.

    After identifying and grouping version conflicts in each group, a cartesian
    product is performed on all groups in order to extract combinations of node
    variant that should be present in the graph at the same time.

    The trimming combination represents the inverse of this product, so that it
    identify the nodes to remove at each graph division::

        >>> groups = [
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

    :param graph: Instance of :class:`Graph`.

    :param variant_groups: List of node identifier lists.

    :return: Generator which yield variant combinations.

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
            variant_identifier = node.package.variant_identifier
            variant_mapping.setdefault(variant_identifier, [])
            variant_mapping[variant_identifier].append(node_identifier)
            variant_mapping[variant_identifier].sort(
                key=lambda _id: _group.index(_id)
            )

        _tuple_group = sorted(
            variant_mapping.values(),
            key=lambda group: _group.index(group[0])
        )
        _groups.append(_tuple_group)

    for combination in itertools.product(*_groups):
        _identifiers = [_id for _group in combination for _id in _group]

        yield GraphCombination(
            graph, nodes_to_remove=set([
                _id for _id in identifiers
                if _id not in _identifiers
            ])
        )


def combined_requirements(graph, nodes):
    """Return combined requirements from *nodes* in *graph*.

    :param graph: Instance of :class:`Graph`.

    :param nodes: List of :class:`Node` instances.

    :raise: :exc:`wiz.exception.GraphResolutionError` if requirements cannot
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
                    "[{}].".format(
                        ", ".join(sorted([requirement.name, _requirement.name]))
                    )
                )

            else:
                requirement.specifier &= _requirement.specifier

    return requirement


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

    :param graph: Instance of :class:`Graph`.

    :param nodes: List of :class:`Node` instances which belong to the
        same definition identifier.

    :return: List of conflict mappings.

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


class Graph(object):
    """Package dependency Graph.

    Requested packages are added recursively as :class:`Node` instances from
    :meth:`requirements <Graph.update_from_requirements>` or :meth:`instances
    <Graph.update_from_package>`::

        >>> graph = Graph(resolver)
        >>> graph.update_from_requirements([Requirement("A >=1, <2")])

    Dependent requirements are traversed using a `Breadth-first
    <https://en.wikipedia.org/wiki/Breadth-first_search>`_ approach so that
    potential errors are recorded in coherent order.

    When a packages cannot be extracted from a requirement, errors are recorded
    and can be retrieved as follows::

        >>> graph.errors()
        {"root": "The requirement 'incorrect' could not be resolved."}

    Conflicting versions and variant groups are recorded and can be retrieved
    as follows::

        >>> graph.conflicting()
        {"B==1.2.0", "B==2.0.0"}

        >>> graph.conflicting_variant_groups()
        [["C[V2]", "C[V1]"], ["D[V2]==1.2.3", "D[V1]==1.2.3"]]

    Conditions will be recorded as :class:`StoredNode` instances.
    Corresponding packages will be added to the graph only if at least one
    package with the same definition identifier has previously been added
    to the graph.

    .. seealso:: :ref:`definition/conditions`

    """

    #: Identify the root of the graph.
    ROOT = "root"

    def __init__(self, resolver):
        """Initialize Graph.

        :param resolver: Instance of :class:`Resolver`.

        """
        self._logger = wiz.logging.Logger(__name__ + ".Graph")
        self._resolver = resolver

        # All nodes created per node identifier.
        self._node_mapping = {}

        # Record the weight and requirement of each link in the graph.
        self._link_mapping = {}

        # List of exception raised per node identifier.
        self._error_mapping = {}

        # List of stored nodes with related conditions.
        self._conditioned_nodes = []

        # Cached set of node identifiers organised per definition identifier.
        self._identifiers_per_definition = {}

        # Cached list of node identifiers with variant organised per definition
        # identifier.
        self._variants_per_definition = {}

        # Cached :class:`collections.Counter` instance which record of
        # occurrences of namespaces from package included in the graph.
        # e.g. Counter({'maya': 2, 'houdini': 1})
        self._namespace_count = collections.Counter()

    def __deepcopy__(self, memo):
        """Ensure that only necessary elements are copied in the new graph.

        Resolver should only be referenced in each copy.

        """
        result = Graph(self._resolver)
        result._node_mapping = copy.deepcopy(self._node_mapping)
        result._link_mapping = copy.deepcopy(self._link_mapping)
        result._error_mapping = copy.deepcopy(self._error_mapping)
        result._conditioned_nodes = copy.deepcopy(self._conditioned_nodes)
        result._identifiers_per_definition = (
            copy.deepcopy(self._identifiers_per_definition)
        )
        result._variants_per_definition = (
            copy.deepcopy(self._variants_per_definition)
        )
        result._namespace_count = copy.deepcopy(self._namespace_count)

        memo[id(self)] = result
        return result

    @property
    def resolver(self):
        """Return resolver instance used to create Graph.

        :return: Instance of :class:`Resolver`.

        """
        return self._resolver

    def node(self, identifier):
        """Return node from *identifier*.

        :param identifier: Unique identifier of the targeted node.

        :return: Instance of :class:`Node` or None if targeted node does not
            exist in the graph.

        """
        return self._node_mapping.get(identifier)

    def nodes(self, definition_identifier=None):
        """Return all nodes in the graph.

        :param definition_identifier: Provide qualified identifier of a
            definition whose nodes must belong to. Default is None which means
            that nodes belonging to any definitions will be returned.

        :return: List of :class:`Node` instances.

        """
        if definition_identifier is not None:
            _definition_id = definition_identifier
            return [
                self.node(identifier) for identifier
                in self._identifiers_per_definition.get(_definition_id, [])
                if self.exists(identifier)
            ]

        return list(self._node_mapping.values())

    def exists(self, identifier):
        """Indicate whether the node *identifier* is in the graph.

        :param identifier: Unique identifier of the targeted node.

        :return: Boolean value.

        """
        return identifier in self._node_mapping.keys()

    def find(self, requirement):
        """Return matching node identifiers in graph for *requirement*.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :return: Set of matching node identifiers.

        """
        identifiers = set()

        for node in self.nodes():
            if wiz.utility.match(requirement, node.package):
                identifiers.add(node.package.identifier)

        return identifiers

    def conditioned_nodes(self):
        """Return all conditioned nodes in the graph.

        A conditioned node is a node which requires one or several requirements
        to be fulfilled before it can be added to the graph.

        :return: List of :class:`StoredNode` instances.

        .. seealso:: :ref:`definition/conditions`

        """
        return self._conditioned_nodes

    def conflicting(self):
        """Return conflicting nodes identifiers.

        A conflict appears when several nodes are found for a single
        definition identifier.

        :return: Set of node identifiers.

        """
        conflicting = set()

        for identifiers in self._identifiers_per_definition.values():
            _identifiers = [
                identifier for identifier in identifiers
                if self.exists(identifier)
            ]

            if len(_identifiers) > 1:
                conflicting.update(_identifiers)

        return conflicting

    def conflicting_variant_groups(self):
        """Return variant groups in graphs.

        A variant group list should contain more than one node identifier which
        belongs at least to two different variant names.

        The variant group list contains unique identifiers and is sorted
        following three criteria:

        1. By number of occurrences of each node identifier in the graph in
           descending order
        2. By the package version in descending order
        3. By the original variant order within the definition.

        :return: Mapping in the form of
            ::

                [
                    ["foo[V2]==0.1.0", "foo[V1]==0.1.0"],
                    ["bar[V2]==2.2.0", "bar[V2]==2.1.5", "bar[V1]==2.1.0"]
                ]

        """
        groups = []

        for identifiers in self._variants_per_definition.values():
            nodes = [self.node(_id) for _id in identifiers if self.exists(_id)]
            variants = set([node.package.variant_identifier for node in nodes])
            if not len(variants) > 1:
                continue

            counter = collections.Counter([node.identifier for node in nodes])

            # TODO: This sorting logic must be improved.
            nodes = sorted(
                nodes,
                key=lambda node: (
                    counter[node.identifier],
                    node.package.version,
                    -nodes.index(node)
                ),
                reverse=True
            )
            groups.append([node.identifier for node in nodes])

        return groups

    def errors(self):
        """Return all encapsulated errors per existing node identifier.

        :return: Mapping if the form of
            ::

                {
                    "foo": "The requirement 'bar' could not be resolved.",
                    ...
                }

        """
        return {
            identifier: error for identifier, error
            in self._error_mapping.items()
            if identifier == self.ROOT or self.exists(identifier)
        }

    def outcoming(self, identifier):
        """Return outcoming node identifiers for node *identifier*.

        :param identifier: Unique identifier of the targeted node.

        :return: List of dependent node identifiers.

        """
        return [
            _identifier for _identifier
            in self._link_mapping.get(identifier, {}).keys()
            if self.exists(_identifier)
        ]

    def link_weight(self, identifier, parent_identifier):
        """Return weight from link between parent and node identifier.

        :param identifier: Unique identifier of the targeted node.

        :param parent_identifier: Unique identifier of parent node.

        :return: Integer value.

        :raise: :exc:`ValueError` if no link is recorded between
            *parent_identifier* and *identifier*.

        """
        key = "weight"
        try:
            return self._link_mapping[parent_identifier][identifier][key]
        except KeyError as error:
            raise ValueError("No link recorded for node: {}".format(error))

    def link_requirement(self, identifier, parent_identifier):
        """Return requirement from link between parent and node identifier.

        :param identifier: Unique identifier of the targeted node.

        :param parent_identifier: Unique identifier of parent node.

        :return: Instance of :class:`packaging.requirements.Requirement`.

        :raise: :exc:`ValueError` if no link is recorded between
            *parent_identifier* and *identifier*.

        """
        key = "requirement"
        try:
            return self._link_mapping[parent_identifier][identifier][key]
        except KeyError as error:
            raise ValueError("No link recorded for node: {}.".format(error))

    def update_from_requirements(self, requirements, detached=False):
        """Update graph from *requirements*.

        One or several :class:`~wiz.package.Package` instances will be
        extracted from *requirements* and :class:`Node` instances will be added
        to graph accordingly. The process will be repeated recursively for
        dependent requirements from newly created packages.

        :param requirements: List of :class:`packaging.requirements.Requirement`
            instances ordered from the most important to the least important.

        :param detached: Indicate whether :class:`Node` instances created for
            *requirements* must be detached from the :attr:`root <Graph.ROOT>`
            level of the graph. Default is False.

        """
        queue = six.moves.queue.Queue()

        wiz.history.record_action(
            wiz.symbol.GRAPH_UPDATE_ACTION,
            graph=self, requirements=requirements
        )

        # Record namespaces from all requirement names.
        self._update_namespace_count(requirements)

        # If not detached, set root node as parent.
        parent_identifier = self.ROOT if not detached else None

        # If not detached, initiate weight depending on existing connections.
        total_connections = len(self._link_mapping.get(self.ROOT, {}).keys())
        weight = total_connections + 1 if not detached else 1

        # Fill up queue from requirements and update the graph accordingly.
        for index, requirement in enumerate(requirements):
            queue.put({
                "requirement": requirement,
                "parent_identifier": parent_identifier,
                "weight": weight + index
            })

        self._process_queue(queue)

    def update_from_package(self, package, requirement, detached=False):
        """Update graph from *package*.

        *package* instance and *requirement* are used to create corresponding
        :class:`Node` instances. The process will be repeated recursively for
        dependent requirements from newly created packages.

        :param package: Instance of :class:`wiz.package.Package`.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement` which led to the
            *package* extraction.

        :param detached: Indicate whether :class:`Node` instance created for
            *package* must be detached from the :attr:`root <Graph.ROOT>` level
            of the graph. Default is False.

        """
        queue = six.moves.queue.Queue()

        wiz.history.record_action(
            wiz.symbol.GRAPH_UPDATE_ACTION,
            graph=self, requirements=[requirement]
        )

        # If not detached, set root node as parent.
        parent_identifier = self.ROOT if not detached else None

        # If not detached, initiate weight depending on existing connections.
        total_connections = len(self._link_mapping.get(self.ROOT, {}).keys())
        weight = total_connections + 1 if not detached else 1

        # Add package to queue to start updating.
        queue.put({
            "requirement": requirement,
            "package": package,
            "parent_identifier": parent_identifier,
            "weight": weight
        })

        self._process_queue(queue)

    def _process_queue(self, queue):
        """Update graph and fetch stored nodes from data contained in *queue*.

        :param queue: Instance of :class:`Queue`.

        """
        while not queue.empty():

            # On first pass, process all nodes in the queue.
            while not queue.empty():
                data = queue.get()

                if data.get("package") is None:
                    self._process_requirement(
                        data.get("requirement"),
                        data.get("parent_identifier"),
                        queue,
                        weight=data.get("weight")
                    )

                else:
                    self._process_package(
                        data.get("package"), data.get("requirement"),
                        data.get("parent_identifier"),
                        queue,
                        weight=data.get("weight")
                    )

            # Then update graph with conditioned nodes stored if necessary.
            for stored_node in self._required_stored_nodes():
                queue.put({
                    "requirement": stored_node.requirement,
                    "package": stored_node.package,
                    "parent_identifier": stored_node.parent_identifier,
                    "weight": stored_node.weight
                })

    def _required_stored_nodes(self):
        """Return :class:`StoredNode` instances which should be added to graph.

        A :class:`StoredNode` instance has been created for each package which
        has one or several conditions.

        :return: List of :class:`StoredNode` instances.

        """
        required = []

        for stored_node in self._conditioned_nodes:
            # Prevent adding stored nodes twice into the graph
            if self.exists(stored_node.identifier):
                continue

            try:
                packages = itertools.chain(*(
                    wiz.package.extract(
                        condition, self.resolver.definition_mapping,
                        namespace_counter=self._namespace_count
                    )
                    for condition in stored_node.package.conditions
                ))

            except wiz.exception.WizError:
                # Do not raise if the condition request is incorrect.
                continue

            if all(self.exists(package.identifier) for package in packages):
                self._logger.debug(
                    "Package '{}' fulfills conditions [{}]".format(
                        stored_node.identifier,
                        ", ".join(
                            str(req) for req in stored_node.package.conditions
                        )
                    )
                )
                required.append(stored_node)

        return required

    def _process_requirement(
        self, requirement, parent_identifier, queue, weight=1
    ):
        """Update graph from *requirement*.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :param parent_identifier: Unique identifier of the parent node.

        :param queue: Instance of :class:`Queue` that will be updated with all
            dependent requirements data.

        :param weight: Number indicating the importance of the dependency
            link from the node to its parent. The lesser this number, the higher
            is the importance of the link. Default is 1.

        """
        self._logger.debug("Update from requirement: {}".format(requirement))

        # Get packages from requirement.
        try:
            packages = wiz.package.extract(
                requirement, self.resolver.definition_mapping,
                namespace_counter=self._namespace_count
            )

        except wiz.exception.WizError as error:
            self._error_mapping.setdefault(parent_identifier, [])
            self._error_mapping[parent_identifier].append(str(error))
            return

        # Create a node for each package if necessary.
        for package in packages:
            self._process_package(
                package, requirement, parent_identifier, queue,
                weight=weight
            )

    def _process_package(
        self, package, requirement, parent_identifier, queue, weight=1
    ):
        """Update graph from *package*.

        :param package: Instance of :class:`wiz.package.Package`.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :param parent_identifier: Unique identifier of the parent node.

        :param queue: Instance of :class:`Queue` that will be updated with all
            dependent requirements data.

        :param weight: Number indicating the importance of the dependency
            link from the node to its parent. The lesser this number, the higher
            is the importance of the link. Default is 1.

        """
        # Ensure that requirement contains namespace.
        requirement = wiz.utility.sanitize_requirement(requirement, package)

        # Update namespace counter from identify namespace if necessary
        namespace, _ = wiz.utility.extract_namespace(requirement)
        if namespace is not None:
            self._namespace_count.update([namespace])

        if not self.exists(package.identifier):

            try:
                # Do not add node to the graph if conditions are unprocessed.
                has_conditions = len(package.conditions) > 0
                if has_conditions and not package.conditions_processed:
                    package.conditions_processed = True

                    self._conditioned_nodes.append(
                        StoredNode(
                            requirement, package,
                            parent_identifier=parent_identifier,
                            weight=weight
                        )
                    )
                    return

                self._create_node(package)

                # Update queue with dependent requirement.
                for index, _requirement in enumerate(package.requirements):
                    queue.put({
                        "requirement": _requirement,
                        "parent_identifier": package.identifier,
                        "weight": index + 1
                    })

            except wiz.exception.RequirementError as error:
                raise wiz.exception.DefinitionError(
                    "Package '{}' is incorrect [{}]"
                    .format(package.identifier, error)
                )

        else:
            # Update variant mapping if necessary
            self._update_variant_mapping(package.identifier)

        node = self._node_mapping[package.identifier]

        if parent_identifier is not None:
            node.add_parent(parent_identifier)

            # Create links with requirement and weight.
            self._create_link(
                node.identifier, parent_identifier, requirement,
                weight=weight
            )

    def _create_node(self, package):
        """Create node in graph from *package*.

        :param package: Instance of :class:`wiz.package.Package`.

        """
        self._logger.debug("Adding package: {}".format(package.identifier))
        self._node_mapping[package.identifier] = Node(package)

        # Record node identifiers per package to identify conflicts.
        _definition_id = package.definition.qualified_identifier
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

        :param identifier: Unique identifier of the targeted node.

        """
        node = self._node_mapping[identifier]
        if node.package.variant_identifier is None:
            return

        # This is not a set because the number of occurrences of each identifier
        # is used to determine its priority within the variant group.
        _definition_id = node.definition.qualified_identifier
        self._variants_per_definition.setdefault(_definition_id, [])
        self._variants_per_definition[_definition_id].append(identifier)

    def _update_namespace_count(self, requirements):
        """Record namespace occurrences from input *requirements*.

        Namespace counter is updated first from input requirements so that each
        requirement can influence package extraction, whatever the requirements'
        order is.

        For instance, if a definition "A" has "foo" and "bar" as available
        namespaces, and another definition "B" has only "foo", then the
        following update will correctly import "foo::A" into the graph::

            >>> self.update_from_requirements([
            ...     Requirement("A"), Requirement("B")
            ... ])

        The namespace counter could then be updated again once each requirement
        is sanitized and a namespace is clearly identified.

        :param requirements: List of :class:`packaging.requirements.Requirement`
            instances.

        """
        mapping = self.resolver.definition_mapping.get("__namespace__", {})

        namespaces = []

        for requirement in requirements:
            namespace, _ = wiz.utility.extract_namespace(requirement)
            if namespace is not None:
                namespaces.append(namespace)
            else:
                namespaces += mapping.get(requirement.name, [])

        self._namespace_count.update(namespaces)

    def remove_node(self, identifier):
        """Remove node from the graph.

        :param identifier: Unique identifier of the targeted node.

        :raise: :exc:`ValueError` if *identifier* does not correspond to any
            existing node in the graph.

        .. warning::

            A lazy deletion is performed as the links are not deleted to save on
            performance.

        """
        try:
            del self._node_mapping[identifier]
        except KeyError:
            raise ValueError("Node can not be removed: {}".format(identifier))

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODE_REMOVAL_ACTION,
            graph=self, node=identifier
        )

    def relink_parents(self, node_removed, requirement=None):
        """Relink node's parents after removing it from the graph.

        Example::

            >>> node = self.node("foo")
            >>> self.remove_node(node.identifier)
            >>> self.relink_parents(node)

        When creating the new links, the same weight connecting the node removed
        to its parents is being used. *requirement* will be used for each new
        link if given, otherwise the same requirement connecting the node
        removed to its parents is being used.

        If a parent node can not be linked to any other node in the graph, an
        error will be recorded.

        :param node_removed: Instance of :class:`Node`.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement` which can be used.
            Default is None.

        :raise: :exc:`ValueError` if *node_removed* still exists in the graph.

        """
        if self.exists(node_removed.identifier):
            raise ValueError(
                "Node must have been removed from graph before relinking "
                "its parent: '{}'".format(node_removed.identifier)
            )

        nodes = None

        # If requirement is given, check all nodes to relink all parents with.
        if requirement is not None:
            nodes = [
                self.node(identifier) for identifier
                in self.find(requirement)
            ]

        for _identifier in node_removed.parent_identifiers:
            # Ignore if parent doesn't exist.
            if not self.exists(_identifier) and not _identifier == self.ROOT:
                continue

            weight = self.link_weight(node_removed.identifier, _identifier)
            _requirement = requirement or self.link_requirement(
                node_removed.identifier, _identifier
            )

            # Check new nodes to link parent with.
            _nodes = nodes or [
                self.node(identifier) for identifier
                in self.find(_requirement)
            ]

            if not len(_nodes):
                self._error_mapping.setdefault(_identifier, [])
                self._error_mapping[_identifier].append(
                    "Requirement '{}' can not be satisfied once '{}' is "
                    "removed from the graph.".format(
                        _requirement, node_removed.identifier,
                    )
                )
                continue

            for _node in _nodes:
                _node.add_parent(_identifier)

                self._create_link(
                    _node.identifier, _identifier, _requirement,
                    weight=weight
                )

    def _create_link(
        self, identifier, parent_identifier, requirement, weight=1
    ):
        """Add dependency link from *parent_identifier* to *identifier*.

        :param identifier: Unique identifier of the package which is added to
            the dependency graph.

        :param parent_identifier: Unique identifier of the targeted package
            which must be linked to the new *identifier*.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :param weight: Number indicating the importance of the dependency
            link from the node to its parent. The lesser this number, the higher
            is the importance of the link. Default is 1.

        .. note::

            If a link already exists between *identifier* and
            *parent_identifier*, the same weight will be preserved.

        """
        self._link_mapping.setdefault(parent_identifier, {})

        # Keep same weight if link exists.
        _link = self._link_mapping[parent_identifier].get(identifier)
        if _link is not None:
            weight = _link["weight"]

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

    def data(self):
        """Return reference mapping.

        :return: Mapping or string containing all information about the graph.

        """
        return {
            "node_mapping": self._node_mapping,
            "link_mapping": self._link_mapping,
            "conditioned_nodes": self._conditioned_nodes,
            "error_mapping": self._error_mapping
        }


class Node(object):
    """Representation of a package within the :class:`Graph`.

    It encapsulates one :class:`~wiz.package.Package` instance with all parent
    package identifiers.

    """

    def __init__(self, package, parent_identifiers=None):
        """Initialize Node.

        :param package: Instance of :class:`wiz.package.Package`.

        :param parent_identifiers: Set of parent identifiers. Default is None.

        """
        self._package = package
        self._parent_identifiers = copy.deepcopy(parent_identifiers) or set()

    def __eq__(self, other):
        """Compare with *other*."""
        if isinstance(other, Node):
            return self.data() == other.data()
        return False

    def __repr__(self):
        """Representing a Node."""
        return "<Node id='{0}' parents=[{1}]>".format(
            self._package.identifier,
            ", ".join(sorted(self._parent_identifiers))
        )

    @property
    def identifier(self):
        """Return identifier of the node.

        :return: String value (e.g. "foo==0.1.0").

        .. note::

            The node identifier is the same as the embedded package instance
            identifier.

        """
        return self._package.identifier

    @property
    def definition(self):
        """Return definition within embedded package instance.

        :return: Instance of :class:`wiz.definition.Definition`.

        """
        return self._package.definition

    @property
    def package(self):
        """Return embedded package instance.

        :return: Instance of :class:`wiz.package.Package`.

        """
        return self._package

    @property
    def parent_identifiers(self):
        """Return set of node identifiers.

        :return: Set of string values.

        """
        return self._parent_identifiers

    def add_parent(self, identifier):
        """Add *identifier* as parent to the node.

        :param identifier: Unique node identifier.

        """
        self._parent_identifiers.add(identifier)

    def data(self):
        """Return reference mapping.

        :return: Mapping containing all information about the node.

        """
        return {
            "package": self._package,
            "parents": sorted(self._parent_identifiers)
        }


class StoredNode(object):
    """Representation of a package which cannot be added to the :class:`Graph`.

    It encapsulates a :class:`~wiz.package.Package` instance with its
    corresponding :class:`~packaging.requirements.Requirement` instance,
    alongside with parent package identifier and weight number assigned.

    A StoredNode instance is used when a package request cannot be immediately
    added to the graph.

    Examples:

    * When a package contains conditions, a StoredNode instance is created for
      this package until the condition can be fulfilled. If the conditions are
      not fulfilled, the package will not be added to the graph.

    """

    def __init__(self, requirement, package, parent_identifier, weight=1):
        """Initialize StoredNode.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :param package: Instance of :class:`wiz.package.Package`.

        :param parent_identifier: Unique identifier if the parent node.

        :param weight: Number indicating the importance of the dependency
            link from the node to its parent. Default is 1.

        """
        self._requirement = requirement
        self._package = package
        self._parent_identifier = parent_identifier
        self._weight = weight

    def __eq__(self, other):
        """Compare with *other*."""
        if isinstance(other, StoredNode):
            return self.data() == other.data()
        return False

    def __repr__(self):
        """Representing a StoredNode."""
        return (
            "<StoredNode id='{0}' requirement='{1}' parent='{2}' weight={3}>"
            .format(
                self._package.identifier,
                self._requirement,
                self._parent_identifier,
                self._weight
            )
        )

    @property
    def identifier(self):
        """Return identifier of the stored node.

        :return: String value (e.g. "foo==0.1.0").

        .. note::

            The node identifier is the same as the embedded package instance
            identifier.

        """
        return self._package.identifier

    @property
    def requirement(self):
        """Return requirement used to extract embedded package instance.

        :return: Instance of :class:`packaging.requirements.Requirement`.

        """
        return self._requirement

    @property
    def package(self):
        """Return embedded package instance.

        :return: Instance of :class:`wiz.package.Package`.

        """
        return self._package

    @property
    def parent_identifier(self):
        """Return unique parent node identifier.

        :return: String value (e.g. "foo==0.1.0").

        """
        return self._parent_identifier

    @property
    def weight(self):
        """Return weight number.

        :return: Integer value.

        """
        return self._weight

    def data(self):
        """Return reference mapping.

        :return: Mapping containing all information about the stored node.

        """
        return {
            "requirement": self._requirement,
            "package": self.package,
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
        """Initialize mapping and build heap."""
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

        :param identifier: Unique node identifier.

        :param distance: Number indicating the importance of the node. A
            shorter distance from the graph root means that the node has a
            higher importance than nodes with longer distances.

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
        """Indicate whether the mapping is empty.

        :return: Boolean value.

        """
        return len(self.keys()) == 0

    def pop_smallest(self):
        """Return item with the shortest distance from graph root and remove it.

        :return: Unique node identifier.

        :raise: :exc:`IndexError` if the object is empty.

        """
        heap = self._heap
        distance, identifier = heappop(heap)

        while identifier not in self or self[identifier] != distance:
            distance, identifier = heappop(heap)

        del self[identifier]
        return identifier

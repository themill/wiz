# :coding: utf-8

from __future__ import absolute_import
import collections
import copy
import itertools
import logging
from heapq import heapify, heappush, heappop

import six.moves

import wiz.config
import wiz.package
import wiz.exception
import wiz.symbol
import wiz.history
from wiz.utility import Requirement


class Resolver(object):
    """Package dependency resolver.

    Compute a ordered list of packages from an initial list of
    :class:`packaging.requirements.Requirement` instances::

        >>> resolver = Resolver()
        >>> resolver.compute_packages([Requirement("foo"), Requirement("bar")])

    An initial :class:`Graph` instance is created from initial requirements with
    all corresponding dependencies.

    If the graph contains conflicting variants, several :class:`Combination`
    instances will be created with a copy of the graph containing onlly one
    variant for each definition included. Only one :class:`Combination` instance
    is created otherwise.

    The resolution process ensures that only one version and one variant of each
    package definition is kept. A graph cannot be resolved if several
    requirements are incompatibles (e.g. "A >= 1" and "A < 1").

    Each :class:`Combination` instance will be generated only if the previous
    one failed to return a solution. If all graph combinations are exhausted and
    no solutions are found, other versions of the conflicting packages will be
    fetched to attempt to resolve the graph.

    """

    def __init__(
        self, definition_mapping, maximum_combinations=None,
        maximum_attempts=None,
    ):
        """Initialize Resolver.

        :param definition_mapping: Mapping regrouping all available definitions
            associated with their unique identifier.

        :param maximum_combinations: Maximum number of combinations which can be
            generated from conflicting variants. Default is None, which means
            that the default value will be picked from the :ref:`configuration
            <configuration>`.

        :param maximum_attempts: Maximum number of resolution attempts before
            raising an error. Default is None, which means  that the default
            value will be picked from the :ref:`configuration <configuration>`.

        """
        self._logger = logging.getLogger(__name__ + ".Resolver")

        self._definition_mapping = definition_mapping

        config = wiz.config.fetch().get("resolver", {})

        default_value = config.get("maximum_combinations", 5)
        self._maximum_combinations = maximum_combinations or default_value

        default_value = config.get("maximum_attempts", 10)
        self._maximum_attempts = maximum_attempts or default_value

        # Iterator containing Combination instances to resolve.
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
        """Return definition mapping used by resolver.

        :return: Mapping containing of all available definitions

        """
        return self._definition_mapping

    @property
    def conflicting_variants(self):
        """Return set of node identifiers with variant used to divide graph.

        :return: Set of node identifiers.

        """
        return self._conflicting_variants

    def compute_packages(self, requirements, namespace_counter=None):
        """Return resolved packages from *requirements*.

        :param requirements: List of :class:`packaging.requirements.Requirement`
            instances.

        :param namespace_counter: instance of :class:`collections.Counter`
            which indicates occurrence of namespaces used as hints for package
            identification. Default is None.

        :raise: :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
            resolved in time.

        """
        graph = Graph(self, namespace_counter=namespace_counter)

        wiz.history.record_action(
            wiz.symbol.GRAPH_CREATION_ACTION,
            graph=graph, requirements=requirements
        )

        # Update the graph.
        graph.update_from_requirements(requirements)

        self.initiate_combinations(graph)

        # Store latest exception to raise if necessary.
        latest_error = None

        # Record the number of failed resolution attempts.
        nb_failures = 0

        while True:
            combination = self.fetch_next_combination()
            if combination is None or nb_failures >= self._maximum_attempts:
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
                        (combination, identifiers)
                        for _, identifiers in error.conflicts
                    ])

                # Divide the graph into new combinations if necessary
                if isinstance(error, wiz.exception.GraphVariantsError):
                    self.extract_combinations(combination.graph)

                self._logger.debug("Failed to resolve graph: {}".format(error))
                latest_error = error
                nb_failures += 1

    def initiate_combinations(self, graph):
        """Initiate combinations iterator from *graph*.

        :param graph: Instance of :class:`Graph`.

        """
        self._logger.debug("Initiate iterator from graph")

        # Initialize iterator.
        self._iterator = iter([])

        # Initialize combinations or simply add graph to iterator.
        if not self.extract_combinations(graph):
            self._iterator = iter([Combination(graph, copy_data=False)])

    def extract_combinations(self, graph):
        """Extract new combinations from conflicting variants in *graph*.

        :param graph: Instance of :class:`Graph`.

        :return: Boolean value indicating whether :class:`Combination` instances
            have been extracted.

        """
        groups = graph.conflicting_variant_groups()
        if not groups:
            self._logger.debug("No variants are conflicting in the graph.")
            return False

        # Record node identifiers from all groups to prevent dividing the graph
        # twice with the same node.
        identifiers = {_id for group in groups for ids in group for _id in ids}
        self._conflicting_variants.update(identifiers)

        self._logger.debug(
            "Conflicting variant groups:\n{}\n".format(
                "\n".join([" * {!r}".format(g) for g in groups])
            )
        )

        wiz.history.record_action(
            wiz.symbol.GRAPH_VARIANT_CONFLICTS_IDENTIFICATION_ACTION,
            graph=graph, variant_groups=groups
        )

        def _generate_combinations():
            """Yield combinations from variant groups."""
            for index, permutation in enumerate(
                _generate_variant_permutations(graph, groups)
            ):
                if index + 1 > self._maximum_combinations:
                    return

                # Flatten permutation groups.
                permutation = {_id for _group in permutation for _id in _group}

                self._logger.debug(
                    "Generate combination with only following variants:\n"
                    "{}\n".format(
                        "\n".join([" * {}".format(_id) for _id in permutation])
                    )
                )

                yield Combination(
                    graph, nodes_to_remove=identifiers.difference(permutation)
                )

        self._iterator = itertools.chain(
            _generate_combinations(),
            self._iterator
        )
        return True

    def fetch_next_combination(self):
        """Return next combination from the iterator.

        :return: Instance of :class:`Combination` or None if iterator is empty.

        """
        try:
            return next(self._iterator)

        except StopIteration:

            # If iterator is empty, check the requirement conflicts to find
            # out if a new graph could be computed with different versions.
            if self.discover_combinations():
                return next(self._iterator)

            self._logger.debug(
                "Impossible to find new graph combinations by downgrading "
                "conflicting versions"
            )

    def discover_combinations(self):
        """Discover new combinations from unsolvable conflicts recorded.

        After exhausting all graph combinations, the unsolvable conflicts
        previously recorded are being used to create new combinations with
        different package versions.

        :return: Boolean value indicating whether :class:`Combination` instances
            have been extracted.

        """
        while True:
            try:
                queue = self._conflicting_combinations
                combination, identifiers = queue.popleft()

            except IndexError:
                return False

            # Prevent mutating original combination as it might be reused to
            # downgrade other conflicting nodes.
            combination = copy.deepcopy(combination)

            # Iterator can be initialized only if all identifiers can be
            # replaced with lower version.
            if not combination.graph.downgrade_versions(identifiers):
                continue

            # Prune unreachable nodes in graph.
            combination.prune_graph()

            # Reset the iterator.
            self.initiate_combinations(combination.graph)

            return True


def _compute_distance_mapping(graph):
    """Return distance mapping for each node of *graph*.

    The mapping indicates the shortest possible distance of each node
    identifier from the :attr:`root <Graph.ROOT>` level of the graph with
    corresponding parent node identifier.

    The distance is defined by the sum of the weights from each node to the
    :attr:`root <Graph.ROOT>` level of the graph.

    This is using `Dijkstra's shortest path algorithm
    <https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm>`_.

    :param graph: Instance of :class:`Graph`.

    :return: Distance mapping.

    .. note::

        When a node is being visited twice, the path with the shortest
        distance is being kept.

    """
    logger = logging.getLogger(__name__ + "._compute_distance_mapping")
    logger.debug("Compute distance mapping.")

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


def _generate_variant_permutations(graph, variant_groups):
    """Yield valid permutations of the variant groups.

    Group containing nodes nearest to the :attr:`root <Graph.ROOT>` level of the
    graph are yield first and variant permutations containing conflicting
    requirements are discarded.

    :param graph: Instance of :class:`Graph`.

    :param variant_groups: Set of tuple containing tuples of node identifiers
        with conflicting variants. It should be in the form of::

            {
                (("foo[V2]==0.1.0",), ("foo[V1]==0.1.0"),),
                (("bar[V2]==2.2.0",), ("bar[V1]==2.2.0", "bar[V1]==2.0.0"))
            }

    :return: Generator of permutations between variant groups.

    :raise: :exc:`ValueError` if one node identifier defined in variant groups
        does not exist in the graph.

    """
    distance_mapping = _compute_distance_mapping(graph)

    # Record permutations previously used.
    permutations_used = set()

    # Compute conflicting matrix to check compatibility between packages.
    conflicting_matrix = _compute_conflicting_matrix(graph, variant_groups)

    # Organise all definition groups per minimum distance to the root level
    # of the graph to prioritizing nodes with the smallest distance to the root
    # node of the graph when computing permutations.
    variant_groups = _sorted_variant_groups(variant_groups, distance_mapping)

    # Extract list containing several variations of the variant groups avoiding
    # conflicting node identifiers.
    variant_groups_list = _extract_optimized_variant_groups(
        variant_groups, conflicting_matrix
    )

    # If all variant groups are conflicting, simply return one permutation of
    # the original variant groups.
    if len(variant_groups_list) == 0:
        yield tuple(tuple(def_grp[0]) for def_grp in variant_groups)
        return

    # Otherwise return permutations for each optimized variant groups.
    for _variant_groups in variant_groups_list:
        for permutation in itertools.product(*_variant_groups):
            _hash = hash(tuple(sorted(permutation)))
            if _hash in permutations_used:
                continue

            permutations_used.add(_hash)
            yield permutation


def _sorted_variant_groups(variant_groups, distance_mapping):
    """Return sorted variant groups using the distance mapping.

    The incoming set is sorted to prioritize definition groups whose nodes are
    nearest to the :attr:`root <Graph.ROOT>` level of the graph. Each definition
    group is also sorted to prioritize variant groups whose nodes are nearest to
    the :attr:`root <Graph.ROOT>` level of the graph.

    :param variant_groups: Set of tuple containing tuples of node identifiers
        with conflicting variants. It should be in the form of::

            {
                (("foo[V2]==0.1.0",), ("foo[V1]==0.1.0"),),
                (("bar[V2]==2.2.0",), ("bar[V1]==2.2.0", "bar[V1]==2.0.0"))
            }

    :param distance_mapping: Mapping indicating the shortest possible distance
        of each node identifier from the :attr:`root <Graph.ROOT>` level of the
        *graph* with its corresponding parent node identifier.

    :return: Tuple containing sorted variant groups.

     """
    _variant_groups = []

    # Sort each definition group using the minimum distance from each variant
    # group in ascending order.
    for definition_group in variant_groups:
        groups = sorted([
            (min([distance_mapping[_id]["distance"] for _id in group]), group)
            for group in definition_group
        ], key=lambda t: (t[0], definition_group.index(t[1])))

        _variant_groups.append(groups)

    # Sort variant groups using the minimum distance from each definition group.
    _variant_groups.sort()

    # Return sorted groups after filtering out the minimum distance.
    return tuple([
        tuple([groups for _, groups in definition_group])
        for definition_group in _variant_groups
    ])


def _extract_optimized_variant_groups(variant_groups, conflicting):
    """Extract list of optimized variant groups skipping conflicting nodes.

    :param variant_groups: :func:`Sorted <_sorted_variant_groups>` variant
        groups tuple. It should be in the form of::

            (
                (("foo[V2]==0.1.0",), ("foo[V1]==0.1.0"),),
                (("bar[V2]==2.2.0",), ("bar[V1]==2.2.0", "bar[V1]==2.0.0"))
            )

    :param conflicting: Mapping recording conflicting status between each
        definition node.

    :return: List of optimized variant groups.

    """
    # Nothing to optimize if there is less than 2 definition groups.
    if len(variant_groups) < 2:
        return [variant_groups]

    variant_groups_list = []

    # Compute optimized variants group for each variant group within each
    # definition group.
    for index, definition_group in enumerate(variant_groups):
        for group in definition_group:

            # Filter out every nodes identifier conflicting with group.
            _group = _filtered_variant_groups(
                variant_groups, callback=lambda _index, _id: not (
                    (_index == index and _id not in group)
                    or any(conflicting.get(id2, {}).get(_id) for id2 in group)
                )
            )

            # Discard filtered group if one entire definition group is
            # conflicting with group.
            if len(_group) != len(variant_groups):
                continue

            # Extract remaining conflict in filtered group if necessary.
            conflicting_groups = []

            identifiers = [_id for grp in _group for ids in grp for _id in ids]
            for identifier in identifiers:
                conflicts = tuple([
                    _id for _id, is_conflicting
                    in conflicting.get(identifier, {}).items()
                    if is_conflicting and _id in identifiers
                ])

                if len(conflicts) and conflicts not in conflicting_groups:
                    conflicting_groups.append(conflicts)

            # If there is no remaining conflicts, record filtered group.
            if len(conflicting_groups) == 0:
                if _group not in variant_groups_list:
                    variant_groups_list.append(_group)

            # Otherwise, record permutations to prevent conflicting nodes to be
            # in the same group.
            for conflicting_group in conflicting_groups:
                _new_group = _filtered_variant_groups(
                    _group, callback=lambda _, _id: _id not in conflicting_group
                )

                # Discard filtered group if one entire definition group is
                # conflicting with group.
                if len(_new_group) != len(variant_groups):
                    continue

                if _new_group not in variant_groups_list:
                    variant_groups_list.append(_new_group)

    return variant_groups_list


def _filtered_variant_groups(variant_groups, callback):
    """Return filtered variant group using *callback*.

    Example::

        >>> groups = (
        ...     (("A[V1]=1", "A[V1]=2"), ("A[V2]",)),
        ...     (("B[V2]",), ("B[V1]",))
        ... )
        >>> _filtered_variant_groups(
        ...     groups, callback=lambda _, _id: _id not in ("A[V1]=2", "B[V1]")
        ... )
        ((("A[V1]=1",), ("A[V2]",)), (("B[V2]",),))

    :param variant_groups: :func:`Sorted <_sorted_variant_groups>` variant
        groups tuple. It should be in the form of::

            (
                (("foo[V2]==0.1.0",), ("foo[V1]==0.1.0"),),
                (("bar[V2]==2.2.0",), ("bar[V1]==2.2.0", "bar[V1]==2.0.0"))
            )

    :param callback: Function returning whether a specific node identifier
        should be kept in the variant groups. It should be in the form of::

            def filter_callback(group_index, identifier):
                \"""Return whether node *identifier* should be kept.\"""
                return group_index == _index and identifier not in _group

    :return: Filtered variant groups.

    """
    filtered_group = []

    for index, definition_group in enumerate(variant_groups):
        _definition_group = []

        for group in definition_group:
            _group = []

            for identifier in group:
                if callback(index, identifier):
                    _group.append(identifier)

            if len(_group):
                _definition_group.append(tuple(_group))

        if len(_definition_group):
            filtered_group.append(tuple(_definition_group))

    return tuple(filtered_group)


def _compute_conflicting_matrix(graph, variant_groups):
    """Compute conflicting matrix for all nodes in variant groups.

    Example::

        >>> groups = {
        ...     (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        ...     (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
        ... }
        >>> _compute_conflicting_matrix(graph, groups)
        {
            "A[V3]": {"B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": True},
            "A[V2]": {"B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": True},
            "A[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True},
            "B[V2]==2": {"A[V3]": True, "A[V2]": True, "A[V1]": False},
            "B[V2]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
            "B[V1]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
        }

    :param graph: Instance of :class:`Graph`.

    :param variant_groups: Set of tuple containing tuples of node identifiers
        with conflicting variants. It should be in the form of::

            {
                (("foo[V2]==0.1.0",), ("foo[V1]==0.1.0"),),
                (("bar[V2]==2.2.0",), ("bar[V1]==2.2.0", "bar[V1]==2.0.0"))
            }

    :return: Matrix recording conflicting status between each definition node.

    """
    mapping = {}

    if len(variant_groups) > 1:
        for group1, group2 in itertools.combinations(variant_groups, r=2):
            # Flatten each definition group as we don't need to distinguish
            # variant clusters.
            group1 = itertools.chain(*group1)
            group2 = itertools.chain(*group2)

            for identifier1, identifier2 in itertools.product(group1, group2):
                node1 = graph.node(identifier1, raising=True)
                node2 = graph.node(identifier2, raising=True)

                conflicting = wiz.utility.check_conflicting_requirements(
                    node1.package, node2.package
                )

                mapping.setdefault(identifier1, {})
                mapping[identifier1][identifier2] = conflicting

                mapping.setdefault(identifier2, {})
                mapping[identifier2][identifier1] = conflicting

    return mapping


def _combined_requirements(graph, nodes):
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
                requirement.extras.update(_requirement.extras)
                requirement.specifier &= _requirement.specifier

    return requirement


def _extract_conflicting_requirements(graph, nodes):
    """Return mapping of conflicting node identifiers per requirement.

    A requirement is conflicting when it is not overlapping with at least one
    other requirement from existing parents of *nodes*.

    :param graph: Instance of :class:`Graph`.

    :param nodes: List of :class:`Node` instances which belong to the
        same definition identifier.

    :return: Mapping in the form of
        ::

            {
                Requirement("foo >=0.1.0, <1"): {"bar", "bim"},
                Requirement("foo >2"): {"baz},
                ...
            }

    :raise: :exc:`ValueError` if nodes do not belong to the same definition.

    """
    # Ensure that definition requirement is the same for all nodes.
    definitions = set(node.definition.qualified_identifier for node in nodes)
    if len(definitions) > 1:
        raise ValueError(
            "All nodes should have the same definition identifier when "
            "attempting to extract conflicting requirements from parent "
            "nodes [{}]".format(", ".join(sorted(definitions)))
        )

    # Identify all parent node identifiers per requirement.
    requirement_mapping = {}

    for node in nodes:
        for identifier in node.parent_identifiers:
            # Filter out non existing nodes from incoming.
            if identifier != graph.ROOT and not graph.exists(identifier):
                continue

            requirement = graph.link_requirement(node.identifier, identifier)
            requirement_mapping.setdefault(requirement, set())
            requirement_mapping[requirement].add(identifier)

    # Identify all conflicting requirements.
    conflicting = set()

    for requirement1, requirement2 in (
        itertools.combinations(requirement_mapping.keys(), 2)
    ):
        if not wiz.utility.is_overlapping(requirement1, requirement2):
            conflicting.update({requirement1, requirement2})

    return {
        requirement: identifiers
        for requirement, identifiers in requirement_mapping.items()
        if requirement in conflicting
    }


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

    def __init__(self, resolver, namespace_counter=None):
        """Initialize Graph.

        :param resolver: Instance of :class:`Resolver`.

        :param namespace_counter: instance of :class:`collections.Counter`
            which indicates occurrence of namespaces used as hints for package
            identification. Default is None.

        """
        self._logger = logging.getLogger(__name__ + ".Graph")
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
        self._definition_cache = {}

        # Cached list of node identifiers with variant organised per definition
        # identifier.
        self._variant_cache = {}

        # Cached :class:`collections.Counter` instance which record of
        # occurrences of namespaces from package included in the graph.
        # e.g. Counter({'maya': 2, 'houdini': 1})
        self._namespace_count = namespace_counter or collections.Counter()

    def __deepcopy__(self, memo):
        """Ensure that only necessary elements are copied in the new graph.

        Resolver should only be referenced in each copy.

        """
        result = Graph(self._resolver)
        result._node_mapping = copy.deepcopy(self._node_mapping)
        result._link_mapping = copy.deepcopy(self._link_mapping)
        result._conditioned_nodes = copy.deepcopy(self._conditioned_nodes)
        result._definition_cache = copy.deepcopy(self._definition_cache)
        result._variant_cache = copy.deepcopy(self._variant_cache)
        result._namespace_count = copy.deepcopy(self._namespace_count)

        # Deepcopy doesn't work on instances inheriting from Exception in
        # Python 2.7, so we need to use shallow copy for mapping containing
        # exceptions until we can switch completely to Python 3.
        result._error_mapping = copy.copy(self._error_mapping)

        memo[id(self)] = result
        return result

    @property
    def resolver(self):
        """Return resolver instance used to create Graph.

        :return: Instance of :class:`Resolver`.

        """
        return self._resolver

    def node(self, identifier, raising=False):
        """Return node from *identifier*.

        :param identifier: Unique identifier of the targeted node.

        :param raising: Indicate whether an exception should be raised if the
            node cannot be fetched in the graph. Default is False.

        :return: Instance of :class:`Node` or None if targeted node does not
            exist in the graph.

        :raise: :exc:`ValueError` if *raising* is True and *identifier* can not
            be found in the graph.

        """
        node = self._node_mapping.get(identifier)
        if raising and node is None:
            raise ValueError("Impossible to fetch '{}'.".format(identifier))

        return node

    def nodes(self, definition_identifier=None):
        """Return all nodes in the graph.

        :param definition_identifier: Provide qualified identifier of a
            definition whose nodes must belong to. Default is None which means
            that nodes belonging to any definitions will be returned.

        :return: List of :class:`Node` instances.

        """
        if definition_identifier is not None:
            return [
                self.node(identifier) for identifier
                in self._definition_cache.get(definition_identifier, [])
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

        for identifiers in self._definition_cache.values():
            _identifiers = [
                identifier for identifier in identifiers
                if self.exists(identifier)
            ]

            if len(_identifiers) > 1:
                conflicting.update(_identifiers)

        return conflicting

    def conflicting_variant_groups(self):
        """Return conflicting variant groups in graphs.

        Conflicting variants occurs when there are at least two packages
        belonging to different variants of one definition in the graph.

        Each group is a tuple composed of tuples to organize node identifiers
        per variant identifier in the order of creation. The tuples regrouping
        nodes per variant identifier are sorted by version in descending order.

        :return: Set of tuple containing tuples of node identifiers.
            ::

                {
                    (("foo[V2]==0.1.0",), ("foo[V1]==0.1.0"),),
                    (("bar[V2]==2.2.0",), ("bar[V1]==2.2.0", "bar[V1]==2.0.0"))
                }
        """
        groups = set()

        for identifiers in self._variant_cache.values():
            nodes = [self.node(_id) for _id in identifiers if self.exists(_id)]

            # Regroup each node per variant identifier.
            variant_group = collections.OrderedDict()
            for node in nodes:
                variant_group.setdefault(node.package.variant_identifier, [])
                variant_group[node.package.variant_identifier].append(node)

            if not len(variant_group) > 1:
                continue

            _group = []

            for nodes in variant_group.values():
                nodes.sort(key=lambda n: n.package.version or "", reverse=True)
                _group.append(tuple([node.identifier for node in nodes]))

            groups.add(tuple(_group))

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
            self._error_mapping[parent_identifier].append(error)
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

        # Update definition cache for quick access to group of nodes
        # belonging to one definition identifier.
        definition_id = package.definition.qualified_identifier
        self._definition_cache.setdefault(definition_id, set())
        self._definition_cache[definition_id].add(package.identifier)

        # Update variant cache if necessary for quick access to group of nodes
        # with variants belonging to one definition identifier.
        if package.variant_identifier is not None:
            self._variant_cache.setdefault(definition_id, [])
            self._variant_cache[definition_id].append(package.identifier)

        # Update namespace counter from identify namespace if necessary.
        if package.namespace is not None:
            self._namespace_count.update([package.namespace])

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODE_CREATION_ACTION,
            graph=self, node=package.identifier
        )

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
                definition_id = node_removed.definition.qualified_identifier
                nodes = self.nodes(definition_identifier=definition_id)
                conflicts = _extract_conflicting_requirements(
                    self, nodes + [node_removed]
                )

                self._error_mapping.setdefault(_identifier, [])
                self._error_mapping[_identifier].append(
                    wiz.exception.GraphConflictsError(conflicts)
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

    def downgrade_versions(self, identifiers):
        """Replace all node *identifiers* in graph with lower versions.

        Combined requirements from parents to each node identifier is computed
        and altered to skip current package version. These new requirements
        are used to extract lower package versions.

        If the identifier does not correspond to any node in the graph or if
        the embedded package is not versioned, the identifier is skipped.

        If no packages can be extracted from new requirements, the identifier
        is also skipped.

        :param identifiers: Set of node identifiers.

        :return: Boolean value indicating whether at least one node have been
            replaced with different versions.

        """
        message = "Attempt to fetch lower versions for '{}'"
        self._logger.debug(message.format(", ".join(identifiers)))

        replacement = {}
        operations = []

        for identifier in identifiers:
            node = self._node_mapping.get(identifier)

            # If the node cannot be fetched or does not have a version, it is
            # impossible to replace it with another version.
            if node is None or node.package.version is None:
                message = "Impossible to fetch another version for '{}'"
                self._logger.debug(message.format(identifier))
                continue

            # Extract combined requirement to node and modify it to exclude
            # current package version.
            requirement = _combined_requirements(self, [node])
            requirement.specifier &= "< {}".format(node.package.version)
            if node.package.variant_identifier is not None:
                requirement.extras = {node.package.variant_identifier}

            try:
                packages = wiz.package.extract(
                    requirement, self.resolver.definition_mapping
                )

            except wiz.exception.RequestNotFound:
                self._logger.debug(
                    "Impossible to fetch another version for '{0}' with "
                    "following request: '{1}'".format(identifier, requirement)
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
                self.update_from_package(package, requirement, detached=True)

        # Step 2: Remove conflicting nodes from graph.
        for node, _, _ in operations:
            self.remove_node(node.identifier)
            self.relink_parents(node)

        self._logger.debug(
            "The following nodes have been updated in the graph:\n"
            "{}\n".format(
                "\n".join([
                    "  * {} -> {}".format(identifier, identifiers)
                    for identifier, identifiers in replacement.items()
                ])
            )
        )

        wiz.history.record_action(
            wiz.symbol.GRAPH_NODES_REPLACEMENT_ACTION,
            graph=self, mapping=replacement
        )

        return True

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
    def package(self):
        """Return embedded package instance.

        :return: Instance of :class:`wiz.package.Package`.

        """
        return self._package

    @property
    def identifier(self):
        """Return identifier of the embedded package instance.

        :return: String value (e.g. "foo==0.1.0").

        """
        return self._package.identifier

    @property
    def definition(self):
        """Return definition of embedded package instance.

        :return: Instance of :class:`wiz.definition.Definition`.

        """
        return self._package.definition

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
        """Return identifier of the embedded package instance.

        :return: String value (e.g. "foo==0.1.0").

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


class Combination(object):
    """Combination of a Package dependency Graph.

    This object operates an initial pruning process on a :class:`Graph` instance
    to ensure that only one variant of each conflicting variant group is
    preserved::

        >>> group = ["A[V3]", "A[V2]", "A[V1]"]
        >>> combination = Combination(graph, nodes_to_remove=group[1:])

    .. note::

        If graph does not have any conflicting variant groups, it might not be
        necessary to remove any nodes.

    Extracting resolved packages from a variant combination can be done in three
    steps:

    * Conflicting versions must be :meth:`resolved
      <Combination.resolve_conflicts>`::

        >>> combination.resolve_conflicts()

    * Remaining nodes must be :meth:`validated
      <Combination.validate>`::

        >>> combination.validate()

    * If previous stages did not raise any error, resolved packages can be
      :meth:`extracted <Combination.extract_packages>`::

        >>> combination.extract_packages()

    .. seealso:: :ref:`definition/variants`

    """

    def __init__(self, graph, nodes_to_remove=None, copy_data=True):
        """Initialize Combination.

        :param graph: Instance of :class:`Graph`.

        :param nodes_to_remove: Set of node identifier from a group of
            conflicting variants which will be removed from the *graph*. Default
            is None which means that no node will be removed from the *graph*.

        :param copy_data: Indicate whether input *graph* will be copied to
            prevent mutating it. Default is True.

        """
        self._logger = logging.getLogger(__name__ + ".Combination")

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

        self._nodes_removed = nodes_to_remove or []

    def __repr__(self):
        """Representing a StoredNode."""
        return (
            "<Combination nodes_removed='{0}'>"
            .format(", ".join(self._nodes_removed))
        )

    def __deepcopy__(self, memo):
        """Ensure that only necessary elements are copied in new combination.
        """
        result = Combination(self._graph)
        result._nodes_removed = self._nodes_removed
        result._distance_mapping = self._distance_mapping

        memo[id(self)] = result
        return result

    @property
    def graph(self):
        """Return embedded graph instance.

        :return: Instance of :class:`Graph`.

        """
        return self._graph

    def _remove_nodes(self, identifiers):
        """Remove nodes corresponding to *identifiers*.

        Remaining unreachable nodes will be pruned.

        :param identifiers: List of node identifiers.

        """
        removed_nodes = []

        for identifier in identifiers:
            node = self._graph.node(identifier)
            self._graph.remove_node(identifier)
            removed_nodes.append(node)

        for node in removed_nodes:
            self._graph.relink_parents(node)

    def resolve_conflicts(self):
        """Attempt to resolve all conflicting versions in embedded graph.

        Conflicting nodes are treated per descending order of distance to the
        :attr:`root <Graph.ROOT>` level of the graph, so that nodes higher in
        the tree have a higher priority over deeper ones.

        Circular conflicts - conflicting node with conflicting parents - will be
        treated last to ensure that higher chance of resolution.

        An exception is raised if the graph can not be resolved.

        :raise: :exc:`wiz.exception.GraphConflictsError` if several node
            requirements are incompatible.

        :raise: :exc:`wiz.exception.GraphVariantsError` if new package
            versions added to the graph during the resolution process lead to
            a division of the graph.

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
        remaining_conflicts = self._update_conflict_queue([conflicts])

        while len(remaining_conflicts) > 0:
            conflict_identifier = remaining_conflicts.popleft()
            node = self._graph.node(conflict_identifier)

            # If node has already been removed from graph, ignore.
            if node is None:
                continue

            # Identify group of nodes conflicting with this node.
            definition_id = node.definition.qualified_identifier
            nodes = self._graph.nodes(definition_identifier=definition_id)
            if len(nodes) < 2:
                continue

            # Compute combined requirements from all conflicting nodes.
            requirement = _combined_requirements(self._graph, nodes)

            # Query common packages from this combined requirements.
            packages = self._discover_packages(
                requirement, nodes, conflict_identifier,
                remaining_conflicts, circular_conflicts
            )
            if packages is None:
                continue

            # If current node is not part of the extracted packages, it will be
            # removed from the graph.
            if not any(
                node.identifier == package.identifier for package in packages
            ):
                self._logger.debug("Remove '{}'".format(node.identifier))
                self._graph.remove_node(node.identifier)

                # Update the graph if necessary
                updated = self._add_packages_to_graph(
                    packages, requirement, nodes
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
                if updated:
                    remaining_conflicts = self._update_conflict_queue(
                        [remaining_conflicts, self._graph.conflicting()],
                        circular_conflicts=circular_conflicts
                    )

    def _update_conflict_queue(self, iterables, circular_conflicts=None):
        """Create new queue with conflicting node identifier lists.

        Duplicated identifiers are removed and all conflicting node identifiers
        are sorted per descending order of distance to the :attr:`root
        <Graph.ROOT>` level of the graph.  If two nodes have the same distance
        to the :attr:`root <Graph.ROOT>` level of the graph, the node identifier
        is used.

        Node identifier included in the *circular_conflicts* set will be sorted
        at the very end of the queue to be treated last.

        :param iterables: Lists of conflicting node identifier.

        :param circular_conflicts: Set of conflicted node identifier which have
            conflicting parents.

        :return: Instance of :class:`collections.deque`.

        """
        distance_mapping = self._fetch_distance_mapping()

        # Remove unreachable nodes from circular conflicts.
        circular_conflicts = set([
            identifier for identifier in circular_conflicts or []
            if distance_mapping.get(identifier, {}).get("distance") is not None
        ])

        # Concatenate conflict lists while ignoring unreachable nodes and
        # identifiers flagged as circular conflicts so it can be added at the
        # end of the queue.
        identifiers = set(
            _id for _identifiers in iterables for _id in _identifiers
            if _id not in circular_conflicts
            and distance_mapping.get(_id, {}).get("distance") is not None
        )

        def _compare(_identifier):
            """Sort identifiers per distance and identifier."""
            return (
                distance_mapping[_identifier]["distance"],
                _identifier
            )

        # Update order by distance.
        conflicts = sorted(identifiers, key=_compare, reverse=True)

        # Appends nodes flagged as circular conflicts
        conflicts.extend(sorted(circular_conflicts, key=_compare, reverse=True))

        # Initiate queue.
        return collections.deque(conflicts)

    def _discover_packages(
        self, requirement, nodes, identifier, remaining_conflicts,
        circular_conflicts
    ):
        """Return packages compatible with combined *requirement*.

        If no packages can be extracted, parent of conflicting *nodes* are
        fetched to find out whether they are part of the remaining conflicts.
        If this is the case, and if node *identifier* hasn't already been
        marked as a circular conflict, None is returned. Otherwise, an error
        is raised.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement`.

        :param nodes: List of :class:`Node` instances.

        :param identifier: Unique identifier of conflicting node currently
            analyzed.

        :param remaining_conflicts: Instance of :class:`collections.deque`
            containing unique identifiers of conflicting nodes.

        :param circular_conflicts: Set of conflicted node identifier which have
            conflicting parents.

        :raise: :exc:`wiz.exception.GraphConflictsError` if no packages have
            been extracted.

        :return: List of :class:`~wiz.package.Package` instances.

        """
        try:
            return wiz.package.extract(
                requirement, self._graph.resolver.definition_mapping
            )

        except wiz.exception.RequestNotFound:
            conflicting = _extract_conflicting_requirements(self._graph, nodes)
            parents = set(itertools.chain(*conflicting.values()))

            # Push conflict at the end of the queue if it has conflicting
            # parents that should be handled first.
            if (
                len(parents.intersection(remaining_conflicts))
                and identifier not in circular_conflicts
            ):
                circular_conflicts.add(identifier)
                remaining_conflicts.append(identifier)
                return

            # Otherwise, raise error and give up on current combination.
            raise wiz.exception.GraphConflictsError(conflicting)

    def _add_packages_to_graph(self, packages, requirement, conflicting_nodes):
        """Add *packages* to embedded graph as detached nodes if necessary.

        Packages which are already recorded as conflict or packages with variant
        which already led to a graph division are skipped.

        :param packages: List of :class:`~wiz.package.Package` instances
            that has been extracted from *requirement*. The list contains more
            than one package only if variants are detected.

        :param requirement: Instance of
            :class:`packaging.requirements.Requirement` which led to the package
            extraction. It is a :func:`combined requirement
            <_combined_requirements>` from all requirements which
            extracted packages embedded in *conflicting_nodes*.

        :param conflicting_nodes: List of :class:`Node` instances representing
            conflicting versions.

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

    def validate(self):
        """Ensure that graph does not have remaining errors.

        If some conflicting errors are found, they would be regrouped and raised
        into one :exc:`~wiz.exception.GraphConflictsError` exception. Other
        type of errors will be regrouped and raised into one
        :exc:`~wiz.exception.GraphInvalidNodesError` exception.

        :raise: :exc:`wiz.exception.GraphInvalidNodesError` if any error is
            found in the embedded graph.

        :raise: :exc:`wiz.exception.GraphConflictsError` if any requirement
            conflict is found in the embedded graph.

        """
        error_mapping = self._graph.errors()
        if len(error_mapping) == 0:
            self._logger.debug("No errors in the graph.")
            return

        _errors = ", ".join(sorted(error_mapping.keys()))
        self._logger.debug("Errors: {}".format(_errors))

        wiz.history.record_action(
            wiz.symbol.GRAPH_ERROR_IDENTIFICATION_ACTION,
            graph=self._graph, errors=list(error_mapping.keys())
        )

        # Extract potential conflicts from errors and combine into one mapping.
        conflicting = {}

        for errors in error_mapping.values():
            for error in errors:
                for requirement, identifiers in getattr(error, "conflicts", []):
                    conflicting.setdefault(requirement, set())
                    conflicting[requirement].update(identifiers)

        # Raise combined exception for conflicts if necessary.
        if len(conflicting):
            raise wiz.exception.GraphConflictsError(conflicting)

        # Otherwise, raise combined exception with remaining errors.
        raise wiz.exception.GraphInvalidNodesError(error_mapping)

    def extract_packages(self):
        """Return sorted list of packages from embedded graph.

        Packages are sorted per descending order of distance to the
        :attr:`root <Graph.ROOT>` level of the graph. If two nodes have the same
        distance to the :attr:`root <Graph.ROOT>` level of the graph, the node
        identifier is used.

        :return: Sorted list of :class:`wiz.package.Package` instances.

        """
        distance_mapping = self._fetch_distance_mapping()

        # Remove unreachable nodes.
        nodes = (
            node for node in self._graph.nodes()
            if distance_mapping.get(node.identifier, {}).get("distance")
            is not None
        )

        def _compare(node):
            """Sort identifiers per distance and identifier."""
            return (
                distance_mapping[node.identifier]["distance"],
                node.identifier
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

    def prune_graph(self):
        """Remove unreachable and invalid nodes from graph.

        First, all unreachable nodes will be removed from the graph. If the
        graph does not contain any unreachable nodes, the pruning process is
        stopped.

        Then, all conditioned nodes added to the graph are being checked and
        removed if conditions are no longer fulfilled. If no conditional nodes
        are removed, the pruning process is stopped.

        These two steps are repeated until no unreachable nodes or no
        conditioned nodes can be removed.

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
        """Remove all unreachable nodes from the graph.

        :return: Boolean value indicating whether one or several nodes have been
            removed.

        """
        distance_mapping = self._fetch_distance_mapping(force_update=True)

        nodes_removed = False

        for node in self._graph.nodes():
            if distance_mapping[node.identifier].get("distance") is None:
                self._logger.debug("Remove '{}'".format(node.identifier))
                self._graph.remove_node(node.identifier)
                nodes_removed = True

        return nodes_removed

    def _trim_unfulfilled_conditions(self):
        """Remove all nodes from the graph with unfulfilled conditions.

        :return: Boolean value indicating whether one or several nodes have been
            removed.

        """
        needs_update = True
        nodes_removed = []

        while needs_update:
            needs_update = False

            for stored_node in self._graph.conditioned_nodes():
                # Ignore if corresponding node has not been added to the graph.
                if not self._graph.exists(stored_node.identifier):
                    continue

                # Otherwise, check whether all conditions are still fulfilled.
                for requirement in stored_node.package.conditions:
                    identifiers = self._graph.find(requirement)

                    if len(identifiers) == 0:
                        self._logger.debug(
                            "Remove '{}' as conditions are no longer "
                            "fulfilled".format(stored_node.identifier)
                        )
                        self._graph.remove_node(stored_node.identifier)
                        nodes_removed.append(stored_node.identifier)
                        needs_update = True
                        break

        return len(nodes_removed) > 0

    def _fetch_distance_mapping(self, force_update=False):
        """Return distance mapping from cached attribute.

        If no distance mapping is available, a new one is generated from
        embedded graph via :func:`_compute_distance_mapping`.

        :param force_update: Indicate whether a new distance mapping should be
            computed, even if one cached mapping is available.

        :return: Distance mapping.

        """
        if self._distance_mapping is None or force_update:
            self._distance_mapping = _compute_distance_mapping(self._graph)

        return self._distance_mapping


class _DistanceQueue(dict):
    """Distance mapping which can be used as a queue.

    Distances are cumulated weights computed between each node and the
    :attr:`root <Graph.ROOT>` level of the graph. Keys of the dictionary are
    node identifiers added into a queue, and values are their respective
    distances.

    The advantage over a standard :mod:`heapq`-based distance queue is that
    distances of node identifiers can be efficiently updated (amortized O(1)).

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

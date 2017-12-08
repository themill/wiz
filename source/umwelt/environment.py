# :coding: utf-8

import mlog
import collections

import umwelt.definition


#: Environment leaf composing the :class:`EnvironmentTree`.
Environment = collections.namedtuple(
    "Environment", ["identifier", "definition", "requirement", "parent"]
)


def create_tree(requirements, definition_mapping):
    """Return the environment dependency tree corresponding to *requirements*.

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
        "Build dependency tree: {!r}".format(requirements)
    )

    tree = EnvironmentTree()

    for requirement in requirements:
        tree.add_branch(requirement, definition_mapping)

    return tree


class EnvironmentTree(object):
    """Environment Tree.

    Represent a directed acyclic graph containing all dependent environment
    mappings.

    """

    def __init__(self):
        """Initialise graph."""
        self._logger = mlog.Logger(__name__ + ".EnvironmentGraph")

        # Record the weight of each link in the graph.
        self._links = dict()

        # Record environments used per identifier.
        self._environments = dict()

    def add_branch(self, requirement, definition_mapping, parent=None):
        """Recursively create branch from *definition_requirement*.

        *requirement* indicates a definition requirement which must
        adhere to `PEP 508 <https://www.python.org/dev/peps/pep-0508>`_.

        *definition_mapping* is a mapping regrouping all available environment
        definition associated with their unique identifier. It is used to
        resolve dependent definition specifiers.

        *parent* can indicate a parent :class:`~umwelt.definition.Definition`.

        Raise :exc:`RuntimeError` is a version conflict is detected.

        """
        self._logger.debug("Create branch for {}".format(requirement))

        definition = umwelt.definition.get(requirement, definition_mapping)

        # Create environment from definition.
        environment = Environment(
            definition.identifier, definition, requirement, parent
        )

        self.check_conflict(environment)

        # Record environments.
        self._environments.setdefault(definition.identifier, [])
        self._environments[definition.identifier].append(environment)

        # Add a dependency link if necessary
        if parent is not None:
            self.add_link(environment.identifier, parent.identifier)

        # Recursively resolve all dependencies
        dependencies = definition.get("dependency", [])
        for dependency_requirement in dependencies:
            self.add_branch(
                dependency_requirement, definition_mapping, parent=definition
            )

    def check_conflict(self, environment):
        """Ensure that *environment* is not conflicting with other environments.

        *environment* is a :class:`Environment` instance.

        Raise :exc:`RuntimeError` is a conflict is detected.

        """
        if environment.identifier not in self._environments.keys():
            return

        conflicting_environment = None

        for _environment in self._environments[environment.identifier]:
            if _environment.version not in _environment.requirement.specifier:
                conflicting_environment = _environment
                break

        if conflicting_environment is not None:
            raise RuntimeError(
                "A version conflict has been detected for '{id!r}'\n"
                " - {env1}\n"
                " - {env2}\n".format(
                    id=environment.requirement,
                    env1=self._display(environment),
                    env2=self._display(conflicting_environment),
                )
            )

    def _display(self, environment):
        """Return formatted identifier for :class:`Environment` instance*."""
        message = "{}".format(environment.requirement)

        if environment.parent is not None:
            message += " [from {!r}]".format(environment.parent.identifier)

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
        self._links.setdefault(parent_identifier, {})

        if identifier in self._links[parent_identifier].keys():
            raise RuntimeError(
                "The definition identified by {!r} is requested twice for the "
                "same parent [{!r}]".format(
                    identifier, parent_identifier
                )
            )

        self._links[parent_identifier][identifier] = weight

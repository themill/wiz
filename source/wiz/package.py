# :coding: utf-8

import collections

import wiz.environment
import wiz.exception


def generate_identifier(environment, variant_name=None):
    """Generate a unique identifier for *environment*.

    *environment* must be an :class:`~wiz.definition.Environment` instance.

    *variant_name* could be the identifier of a variant mapping.

    """
    if variant_name is not None:
        variant_name = "[{}]".format(variant_name)

    return "{environment}{variant}=={version}".format(
        environment=environment.identifier,
        version=environment.version,
        variant=variant_name or ""
    )


def extract(requirement, environment_mapping):
    """Extract list of :class:`Package` instances from *requirement*.

    The best matching :class:`~wiz.definition.Environment` version instances
    corresponding to the *requirement* will be used.

    If this environment contains variants, a :class:`Package` instance will be
    returned for each combined variant.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    """
    environment = wiz.environment.get(requirement, environment_mapping)

    # Extract variants from environment if available.
    variants = environment.variant

    # Extract and return the requested variant if necessary.
    if len(requirement.extras) > 0:
        variant_identifier = next(iter(requirement.extras))
        variant_mapping = reduce(
            lambda res, mapping: dict(res, **{mapping["identifier"]: mapping}),
            variants, {}
        )

        if variant_identifier not in variant_mapping.keys():
            raise wiz.exception.RequestNotFound(
                "The variant '{}' could not been resolved for {}.".format(
                    variant_identifier, environment
                )
            )

        return [Package(environment, variant_mapping[variant_identifier])]

    # Simply return the main environment if no variants is available.
    elif len(variants) == 0:
        return [Package(environment)]

    # Otherwise, extract and return all possible variants.
    else:
        return map(lambda variant: Package(environment, variant), variants)


class Package(collections.Mapping):
    """Package object."""

    def __init__(self, environment, variant=None):
        """Initialise Package from *environment*.

        *environment* must be a valid :class:`wiz.definition.Environment`
        instance.

        *variant* could be a valid variant mapping which should have at least
        an 'identifier' keyword.

        In case of conflicted elements in both mappings, the elements from the
        *variant* will have priority over elements from *environment*.

        """
        self._mapping = dict()

        variant_mapping = {}

        if variant is not None:
            variant_mapping = {
                "identifier": variant.identifier,
                "data": wiz.environment.combine_data(environment, variant),
                "alias": wiz.environment.combine_alias(environment, variant),
                "requirement": (
                    environment.requirement + variant.requirement
                )
            }

        self._mapping = {
            "identifier": generate_identifier(
                environment, variant_name=variant_mapping.get("identifier")
            ),
            "environment": environment.identifier,
            "description": environment.description,
            "alias": variant_mapping.get("alias") or environment.alias,
            "data": variant_mapping.get("data") or environment.data,
            "requirement": (
                variant_mapping.get("requirement") or environment.requirement
            ),
        }

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def environment(self):
        """Return environment identifier."""
        return self.get("environment")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    @property
    def alias(self):
        """Return alias mapping."""
        return self.get("alias", {})

    @property
    def data(self):
        """Return data mapping."""
        return self.get("data", {})

    @property
    def requirement(self):
        """Return requirement list."""
        return self.get("requirement", [])

    def __str__(self):
        """Return string representation."""
        return "'{}'".format(self.identifier)

    def __getitem__(self, key):
        """Return value for *key*."""
        return self._mapping[key]

    def __iter__(self):
        """Iterate over all keys."""
        for key in self._mapping:
            yield key

    def __len__(self):
        """Return count of keys."""
        return len(self._mapping)

# :coding: utf-8

import abc
import collections
import copy
import json

import wiz.exception
import wiz.symbol
import wiz.utility


class Mapping(collections.Mapping):
    """Immutable mapping mixin object."""

    def __init__(self, *args, **kwargs):
        """Initialise mapping."""
        super(Mapping, self).__init__()
        self._mapping = copy.deepcopy(dict(*args, **kwargs))

        # Sanitize all elements of the mapping.
        self._sanitize_version()
        self._sanitize_requirements()
        self._sanitize_conditions()

    def _sanitize_version(self):
        """Ensure version is a :class:`packaging.version.Version` instance.
        """
        version = self._mapping.get("version")

        try:
            if version and not isinstance(version, wiz.utility.Version):
                self._mapping["version"] = wiz.utility.get_version(version)

        except wiz.exception.InvalidVersion:
            raise wiz.exception.IncorrectDefinition(
                "{label} has an incorrect version [{version}]".format(
                    label=self._label(),
                    version=self._mapping["version"]
                )
            )

    def _sanitize_requirements(self):
        """Ensure requirements are :class:`packaging.requirement.Requirement`
        instances.
        """
        size = len(self._mapping.get("requirements", []))

        try:
            for index in range(size):
                requirement = self._mapping["requirements"][index]

                if not isinstance(requirement, wiz.utility.Requirement):
                    self._mapping["requirements"][index] = (
                        wiz.utility.get_requirement(requirement)
                    )

        except wiz.exception.InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "{label} contains an incorrect package requirement "
                "[{error}]".format(
                    label=self._label(),
                    error=exception
                )
            )

    def _sanitize_conditions(self):
        """Ensure conditions are :class:`packaging.requirement.Requirement`
        instances.
        """
        size = len(self._mapping.get("conditions", []))

        try:
            for index in range(size):
                condition = self._mapping["conditions"][index]

                if not isinstance(condition, wiz.utility.Requirement):
                    self._mapping["conditions"][index] = (
                        wiz.utility.get_requirement(condition)
                    )

        except wiz.exception.InvalidRequirement as exception:
            raise wiz.exception.IncorrectDefinition(
                "{label} contains an incorrect package condition "
                "[{error}]".format(
                    label=self._label(),
                    error=exception
                )
            )

    def _label(self):
        """Return object label to include in exception messages."""
        return "The {type} '{identifier}'".format(
            type=self.__class__.__name__.lower(),
            identifier=self._mapping.get("identifier"),
        )

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def version(self):
        """Return version."""
        return self.get("version", wiz.symbol.UNSET_VALUE)

    @property
    def description(self):
        """Return description."""
        return self.get("description", wiz.symbol.UNSET_VALUE)

    @property
    def namespace(self):
        """Return namespace."""
        return self.get("namespace")

    @property
    def environ(self):
        """Return environ mapping."""
        return self.get("environ", {})

    @property
    def command(self):
        """Return command mapping."""
        return self.get("command", {})

    @property
    def system(self):
        """Return system constraint mapping."""
        return self.get("system", {})

    @property
    def requirements(self):
        """Return requirement list."""
        return self.get("requirements", [])

    @property
    def conditions(self):
        """Return conditions."""
        return self.get("conditions", [])

    def copy(self, *args, **kwargs):
        """Return copy of instance."""
        return self.__class__(*args, **kwargs)

    def set(self, element, value):
        """Returns copy of instance with *element* set to *value*.
        """
        _mapping = self.to_dict()
        _mapping[element] = value
        return self.copy(**_mapping)

    def update(self, element, value):
        """Returns copy of instance with *element* mapping updated with *value*.

        Raise :exc:`ValueError` if *element* is not a dictionary.

        """
        _mapping = self.to_dict()
        _mapping.setdefault(element, {})

        if not isinstance(_mapping[element], dict):
            raise ValueError(
                "Impossible to update '{}' as it is not a "
                "dictionary.".format(element)
            )

        _mapping[element].update(value)
        return self.copy(**_mapping)

    def extend(self, element, values):
        """Returns copy of instance with *element* list extended with *values*.

        Raise :exc:`ValueError` if *mapping* is not a list.

        """
        _mapping = self.to_dict()
        _mapping.setdefault(element, [])

        if not isinstance(_mapping[element], list):
            raise ValueError(
                "Impossible to extend '{}' as it is not a list.".format(element)
            )

        _mapping[element].extend(values)
        return self.copy(**_mapping)

    def insert(self, element, value, index):
        """Returns copy of instance with *value* inserted in *element* list.

        *index* should be the index number at which the *value* should be
        inserted.

        Raise :exc:`ValueError` if *mapping* is not a list.

        """
        _mapping = self.to_dict()
        _mapping.setdefault(element, [])

        if not isinstance(_mapping[element], list):
            raise ValueError(
                "Impossible to insert '{}' in '{}' as it is not "
                "a list.".format(value, element)
            )

        _mapping[element].insert(index, value)
        return self.copy(**_mapping)

    def remove(self, element):
        """Returns copy of instance without *element*."""
        _mapping = self.to_dict()
        if element not in _mapping.keys():
            return self

        del _mapping[element]
        return self.copy(**_mapping)

    def remove_key(self, element, value):
        """Returns copy of instance without key *value* from *element* mapping.

        If *element* mapping is empty after removing *value*, the *element* key
        will be removed.

        Raise :exc:`ValueError` if *element* is not a dictionary.

        """
        _mapping = self.to_dict()
        if element not in _mapping.keys():
            return self

        if not isinstance(_mapping[element], dict):
            raise ValueError(
                "Impossible to remove key from '{}' as it is not a "
                "dictionary.".format(element)
            )

        if value not in _mapping[element].keys():
            return self

        del _mapping[element][value]
        if len(_mapping[element]) == 0:
            del _mapping[element]

        return self.copy(**_mapping)

    def remove_index(self, element, index):
        """Returns copy of instance without *index* from *element* list.

        If *element* list is empty after removing *index*, the *element* key
        will be removed.

        Raise :exc:`ValueError` if *element* is not a list.

        """
        _mapping = self.to_dict()
        if element not in _mapping.keys():
            return self

        if not isinstance(_mapping[element], list):
            raise ValueError(
                "Impossible to remove index from '{}' as it is not a "
                "list.".format(element)
            )

        if index >= len(_mapping[element]):
            return self

        del _mapping[element][index]
        if len(_mapping[element]) == 0:
            del _mapping[element]

        return self.copy(**_mapping)

    def to_dict(self, serialize_content=False):
        """Return corresponding dictionary.

        *serialize_content* indicates whether all mapping values should be
        serialized.

        """
        _mapping = copy.deepcopy(self._mapping)
        if serialize_content:
            return _serialize_content(_mapping)

        return _mapping

    def to_ordered_dict(self, serialize_content=False):
        """Return corresponding ordered dictionary.

        *serialize_content* indicates whether all mapping values should be
        serialized.

        """
        mapping = self.to_dict()
        content = collections.OrderedDict()

        def _extract(element, _identifier=None):
            """Extract *element* from mapping."""
            # Remove element from mapping if identifier is specified.
            if _identifier is not None:
                mapping.pop(_identifier)

            if isinstance(element, list) and len(element) > 0:
                return [_extract(item) for item in element]

            elif isinstance(element, dict) and len(element) > 0:
                return {_id: _extract(item) for _id, item in element.items()}

            elif isinstance(element, Mapping):
                return element.to_ordered_dict(
                    serialize_content=serialize_content
                )

            else:
                if serialize_content:
                    return _serialize_content(element)
                return element

        for identifier in self._ordered_keywords:
            if identifier not in mapping.keys():
                continue

            content[identifier] = _extract(mapping[identifier], identifier)

        content.update(mapping)
        return content

    @abc.abstractmethod
    def _ordered_keywords(self):
        """Return ordered keywords"""

    def encode(self):
        """Return serialized definition data."""
        return json.dumps(
            self.to_ordered_dict(serialize_content=True),
            indent=4,
            separators=(",", ": "),
            ensure_ascii=False
        )

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

    def __repr__(self):
        """Representation of the mapping."""
        return "{}({})".format(
            self.__class__.__name__,
            self.to_dict(serialize_content=True)
        )


def _serialize_content(element):
    """Return recursively serialized *element*.

    *element* can be a of any types (:class:`Mapping`, dict, list, ...)

    """
    if isinstance(element, list):
        return [_serialize_content(item) for item in element]

    elif isinstance(element, dict):
        return {_id: _serialize_content(item) for _id, item in element.items()}

    elif isinstance(element, Mapping):
        return element.to_dict(serialize_content=True)

    # Boolean values are not serialized.
    elif isinstance(element, bool):
        return element

    return str(element)

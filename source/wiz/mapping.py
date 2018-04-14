# :coding: utf-8

import json
import collections
import abc

import wiz.symbol
import wiz.exception


class Mapping(collections.Mapping):
    """Immutable mapping mixin object."""

    def __init__(self, *args, **kwargs):
        """Initialise mapping."""
        super(Mapping, self).__init__()
        self._mapping = dict(*args, **kwargs)

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def version(self):
        """Return version."""
        return self.get("version", wiz.symbol.UNKNOWN_VALUE)

    @property
    def description(self):
        """Return description."""
        return self.get("description", wiz.symbol.UNKNOWN_VALUE)

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

    def to_dict(self, serialize_content=False):
        """Return corresponding dictionary.

        *serialize_content* indicates whether all mapping values should be
        serialized.

        """
        if serialize_content:
            return _serialize(self._mapping.copy())

        return self._mapping.copy()

    def to_ordered_dict(self, serialize_content=False):
        """Return corresponding ordered dictionary.

        *serialize_content* indicates whether all mapping values should be
        serialized.

        """
        mapping = self.to_dict(serialize_content=serialize_content)
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
                return element

        for identifier in self._ordered_identifiers:
            if identifier not in mapping.keys():
                continue

            content[identifier] = _extract(mapping[identifier], identifier)

        content.update(mapping)
        return content

    @abc.abstractmethod
    def _ordered_identifiers(self):
        """Return ordered identifiers"""

    def encode(self):
        """Return serialized definition data."""
        return json.dumps(
            self.to_ordered_dict(),
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


def _serialize(element):
    """Return serialized version of *element*.

    *element* can be a of any types (:class:`Mapping`, dict, list, ...)

    """
    if isinstance(element, list):
        return [_serialize(item) for item in element]

    elif isinstance(element, dict):
        return {_id: _serialize(item) for _id, item in element.items()}

    elif isinstance(element, Mapping):
        return element.to_dict(serialize_content=True)

    return str(element)

# :coding: utf-8

import packaging.requirements
from packaging.requirements import (
    L, Combine, Word, ZeroOrMore, ALPHANUM, Optional, EXTRAS,
    URL_AND_MARKER, VERSION_AND_MARKER, stringStart, stringEnd
)
from packaging.requirements import Requirement

import wiz.symbol

# Extend requirement's expression to allow namespace separators as a valid
# identifier (e.g. "foo::test", "::test").
PUNCTUATION = Word("-_.")
NAME = ALPHANUM + ZeroOrMore(ALPHANUM | (ZeroOrMore(PUNCTUATION) + ALPHANUM))
NAME_SEPARATOR = L(wiz.symbol.NAMESPACE_SEPARATOR)
IDENTIFIER = Combine(
    ZeroOrMore(Optional(NAME) + NAME_SEPARATOR) + NAME
)

packaging.requirements.REQUIREMENT = (
    stringStart + IDENTIFIER("name") + Optional(EXTRAS)
    + (URL_AND_MARKER | VERSION_AND_MARKER) + stringEnd
)


def _display_requirement(_requirement):
    """Improve readability when displaying Requirement instance.

    Before::

        >>> Requirement("nuke>=10,<11")
        <Requirement('nuke<11,>=10')>

    After::

        >>> Requirement("nuke>=10,<11")
        <Requirement('nuke >=10, <11')>

    """
    content = _requirement.name

    variant = ",".join(_requirement.extras)
    if len(variant) > 0:
        content += "[{}]".format(variant)

    if len(_requirement.specifier) > 0:
        content += " " + ", ".join(sorted([
            str(specifier) for specifier in _requirement.specifier
        ], reverse=True))

    return content


#: Monkeypatch magic method to improve readability of serialized item.
Requirement.__str__ = _display_requirement

#: Monkeypatch magic methods to allow comparison between instances.
Requirement.__eq__ = lambda self, other: (
    str(self) == str(other) if isinstance(other, Requirement) else False
)
Requirement.__ne__ = lambda self, other: not (self == other)
Requirement.__hash__ = lambda self: hash(str(self))

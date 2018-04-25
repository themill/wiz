# :coding: utf-8

import base64
import json
import zlib


import wiz.mapping


def encode(element):
    """Return serialized and encoded *element*.

    *element* is serialized first, then encoded into :term:`base64`.

    Raises :exc:`TypeError` if *element* is not JSON serializable.

    """
    return base64.b64encode(zlib.compress(json.dumps(element)))


def decode(element):
    """Return deserialized and decoded *element*.

    *element* is decoded first from :term:`base64`, then deserialized.

    Raises :exc:`TypeError` if *element* cannot be decoded or deserialized..

    """
    return json.loads(zlib.decompress(base64.b64decode(element)))


def serialize(element):
    """Return recursively serialized *element*.

    *element* can be a of any types (:class:`Mapping`, dict, list, ...)

    """
    if isinstance(element, list):
        return [serialize(item) for item in element]

    elif isinstance(element, dict):
        return {_id: serialize(item) for _id, item in element.items()}

    elif isinstance(element, wiz.mapping.Mapping):
        return element.to_dict(serialize_content=True)

    return str(element)

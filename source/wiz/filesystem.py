# :coding: utf-8

import os
import errno
import io
import unicodedata
import re
import gzip
import base64
import json
import zlib

try:
    to_unicode = unicode
except NameError:
    to_unicode = str


def export(path, content, compressed=False):
    """Create file from *content* in *path*."""
    ensure_directory(os.path.dirname(path))

    if compressed:
        with gzip.open(path, "wb") as outfile:
            outfile.write(content)

    else:
        with io.open(path, "w", encoding="utf8") as outfile:
            outfile.write(to_unicode(content))


def ensure_directory(path):
    """Ensure directory exists at *path*."""
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise

        if not os.path.isdir(path):
            raise


def sanitise_value(value, substitution_character="_", case_sensitive=True):
    """Return *value* suitable for use with filesystem.

    Replace awkward characters with *substitution_character*. Where possible,
    convert unicode characters to their closest "normal" form.

    If not *case_sensitive*, then also lowercase value.

    """
    if isinstance(value, str):
        value = value.decode("utf-8")

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore")
    value = re.sub(r"[^\w._\-\\/:%]", substitution_character, value)
    value = value.strip()

    if not case_sensitive:
        value = value.lower()

    return unicode(value)


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

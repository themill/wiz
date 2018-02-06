# :coding: utf-8

import os
import errno
import io
import unicodedata
import re

try:
    to_unicode = unicode
except NameError:
    to_unicode = str


def export(path, content):
    """Create file from *content* in *path*."""
    ensure_directory(os.path.dirname(path))

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

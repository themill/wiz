# :coding: utf-8

import os
import errno
import io
import unicodedata
import re
import gzip

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


def is_accessible(folder_path):
    """Indicate whether the *folder_path* is accessible."""
    return os.path.isdir(folder_path) and os.access(folder_path, os.R_OK)


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

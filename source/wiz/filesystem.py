# :coding: utf-8

import os
import errno
import io
import unicodedata
import re
import gzip
import pwd
import getpass

import wiz.exception

try:
    to_unicode = unicode
except NameError:
    to_unicode = str


def get_name():
    """Fetch user full name from password database entry.

    Return None if name cannot be returned.

    """
    try:
        return pwd.getpwnam(getpass.getuser()).pw_gecos
    except KeyError:
        return


def export(path, content, compressed=False, overwrite=False):
    """Create file from *content* in *path*.

    *overwrite* indicate whether any existing path will be overwritten. Default
    is False.

    Raise :exc:`wiz.exception.FileExists` if overwrite is False and *path*
    already exists.

    """
    # Ensure that "~" is resolved if necessary and that the relative path is
    # always converted into a absolute path.
    path = os.path.abspath(os.path.expanduser(path))

    if os.path.isfile(path) and not overwrite:
        raise wiz.exception.FileExists("{!r} already exists.".format(path))

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
    # Explicitly indicate that path should be a directory as default OSError
    # raised by 'os.makedirs' just indicates that the file exists, which is a
    # bit confusing for user.
    if os.path.isfile(path):
        raise OSError("'{}' should be a directory".format(path))

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

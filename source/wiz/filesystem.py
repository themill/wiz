# :coding: utf-8

import os
import errno
import io
import unicodedata
import re
import gzip
import pwd
import getpass

import six

import wiz.exception


def get_name():
    """Fetch user full name from password database entry.

    :return: User name of None if name cannot be returned.

    """
    try:
        return pwd.getpwnam(getpass.getuser()).pw_gecos
    except KeyError:
        return


def export(path, content, compressed=False, overwrite=False):
    """Create file from *content* in *path*.

    :param path: Target path to save the file.

    :param content: Content string to write in *path*.

    :param compressed: Indicate whether exported file should be compressed.
        Default is False.

    :param overwrite: Indicate whether any existing path will be overwritten.
        Default is False.

    :raise: :exc:`wiz.exception.FileExists` if overwrite is False and *path*
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
            outfile.write(six.text_type(content))


def is_accessible(folder_path):
    """Indicate whether the folder path is accessible.

    :param folder_path: Path to the folder to analyze.

    :return: Boolean value.

    """
    return os.path.isdir(folder_path) and os.access(folder_path, os.R_OK)


def ensure_directory(path):
    """Ensure directory exists at *path*.

    :param path: Path to the folder to create.

    :raise: :exc:`OSError` is path is a file.

    """
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


def sanitize_value(value, substitution_character="_", case_sensitive=True):
    """Return *value* suitable for use with filesystem.

    :param value: String value to sanitize.

    :param substitution_character: Symbol to replace awkward characters with.
        Default is underscore.

    :param case_sensitive: Indicate whether case should be preserved or if
        value should be converted to lowercase. Default is True.

    :return: Sanitized value.

    """
    value = unicodedata.normalize("NFKD", six.u(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w._\-\\/:%]", substitution_character, value)
    value = value.strip()

    if not case_sensitive:
        value = value.lower()

    return six.text_type(value)

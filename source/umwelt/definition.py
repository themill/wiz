# :coding: utf-8

import os
import collections
import json

import mlog


def discover(paths, max_depth=None):
    """Discover and yield environment definitions found under *paths*.

    If *max_depth* is None, search all sub-trees under each path for
    environment files in JSON format. Otherwise, only search up to *max_depth*
    under each path. A *max_depth* of 0 should only search directly under the
    specified paths.

    """
    logger = mlog.Logger(__name__ + ".discover")

    for path in paths:
        # Ignore empty paths that could resolve to current directory.
        path = path.strip()
        if not path:
            logger.debug("Skipping empty path.")
            continue

        path = os.path.abspath(path)
        logger.debug(
            "Searching under {!r} for environment definition files."
            .format(path)
        )
        initial_depth = path.rstrip(os.sep).count(os.sep)
        for base, _, filenames in os.walk(path):
            depth = base.count(os.sep)
            if max_depth is not None and (depth - initial_depth) > max_depth:
                continue

            for filename in filenames:
                _, extension = os.path.splitext(filename)
                if extension != ".json":
                    continue

                environment_path = os.path.join(base, filename)
                logger.debug(
                    "Discovered environment definition file {!r}.".format(
                        environment_path
                    )
                )

                try:
                    environment = load(environment_path)
                except (IOError, ValueError, TypeError):
                    logger.warning(
                        "Error occurred trying to load environment definition "
                        "from {!r}".format(environment_path),
                        traceback=True
                    )
                    continue
                else:
                    logger.debug(
                        "Loaded environment definition {!r} from {!r}."
                        .format(environment.identifier, environment_path)
                    )
                    yield environment


def load(path):
    """Load and return :class:`Environment` from *path*."""
    with open(path, "r") as stream:
        environment_data = json.load(stream)
        # TODO: Validate with JSON-Schema.
        environment = Definition(**environment_data)
        return environment


class Definition(collections.MutableMapping):
    """Environment Definition."""

    def __init__(self, *args, **kwargs):
        """Initialise environment definition."""
        super(Definition, self).__init__()
        self._mapping = {}
        self.update(*args, **kwargs)

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier", "unknown")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    @property
    def version(self):
        """Return version."""
        return self.get("version", "unknown")

    def __str__(self):
        """Return string representation."""
        return "{}({!r}, {!r})".format(
            self.__class__.__name__, self.identifier, self._mapping
        )

    def __getitem__(self, key):
        """Return value for *key*."""
        return self._mapping[key]

    def __setitem__(self, key, value):
        """Set *value* for *key*."""
        self._mapping[key] = value

    def __delitem__(self, key):
        """Delete *key*."""
        del self._mapping[key]

    def __iter__(self):
        """Iterate over all keys."""
        for key in self._mapping:
            yield key

    def __len__(self):
        """Return count of keys."""
        return len(self._mapping)

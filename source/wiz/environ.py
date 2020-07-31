# :coding: utf-8

import itertools
import os
import re

import wiz.config

#: Compiled regular expression to identify environment variables in string.
ENV_PATTERN = re.compile(r"\${(\w+)}|\$(\w+)")


def initiate(mapping=None):
    """Return the minimal environment mapping to augment.

    *mapping* can be a custom environment mapping which will be added to the
    initial environment.

    .. seealso:: :ref:`configuration/initial_environment`

    """
    config = wiz.config.fetch()
    environ = config.get("environ", {}).get("initial", {})

    for key in config.get("environ", {}).get("passthrough", []):
        value = os.environ.get(key)

        if value:
            environ[key] = value

    if mapping is not None:
        environ.update(**mapping)

    return environ


def sanitise(mapping):
    """Return sanitised environment *mapping*.

    Resolve all key references within *mapping* values and remove all
    self-references::

        >>> sanitise({
        ...     "PLUGIN": "${HOME}/.app:/path/to/somewhere:${PLUGIN}",
        ...     "HOME": "/usr/people/me"
        ... })

        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/somewhere"
        }

    """
    _mapping = {}

    # Remove all self reference environment variables in values with trailing
    # path separator (e.g. {"PATH": "/path/to/somewhere:${PATH}"}).
    pattern = r"(\${{{0}}}:?|:?\${{{0}}}|\${0}:?|:?\${0})"

    for key, value in mapping.items():
        _mapping[key] = re.sub(pattern.format(key), lambda _: "", value)

    # Last pass across mapping to substitute remaining variables.
    for key, value in _mapping.items():
        _mapping[key] = substitute(value, _mapping)

    return _mapping


def contains(text, name):
    """Indicate whether *text* contains a reference to variable *name*.

    *text* is a string which can contain environment variable
    (e.g. "${PATH}/to/somewhere")

    *name* is the name of an environment variable (e.g. "PATH")

    Example::

        >>> contains("${HOME}/path/to/data", "HOME")

        True

    """
    return name in itertools.chain(*ENV_PATTERN.findall(text))


def substitute(text, environment):
    """Substitute all environment variables in *text* from *environment*.

    *text* is a string which can contain environment variable
    (e.g. "${PATH}/to/somewhere")

    *environment* is a mapping of environment variables with their respective
    values.

    Example::

        >>> substitute("${HOME}/path/to/data", {"HOME": "/usr/people/john-doe"})

        /usr/people/john-doe/path/to/data

    """

    def _substitute(match):
        origin = match.group(0)
        name = next(item for item in match.groups() if item is not None)
        return environment.get(name, origin)

    return ENV_PATTERN.sub(_substitute, text)

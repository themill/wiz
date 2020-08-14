# :coding: utf-8

import itertools
import os
import re

import wiz.config

#: Compiled regular expression to identify environment variables in string.
ENV_PATTERN = re.compile(r"\${(\w+)}|\$(\w+)")


def initiate(mapping=None):
    """Return the minimal environment mapping to augment.

    :param mapping: Custom environment mapping which will be added to the
        initial environment. Default is None.

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


def sanitize(mapping):
    """Return sanitized environment *mapping*.

    Resolve all key references within *mapping* values and remove all
    self-references::

        >>> sanitize({
        ...     "PLUGIN": "${HOME}/.app:/path/to/somewhere:${PLUGIN}",
        ...     "HOME": "/usr/people/me"
        ... })

        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/somewhere"
        }

    :param mapping: Environment mapping to sanitize.

    :return: Sanitized environment mapping.

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

    Example::

        >>> contains("${HOME}/path/to/data", "HOME")

        True

    :param text: String which can contain environment variable
        (e.g. "${PATH}/to/somewhere").

    :param name: Name of an environment variable (e.g. "PATH").

    :return: Boolean value.

    """
    return name in itertools.chain(*ENV_PATTERN.findall(text))


def substitute(text, environment):
    """Substitute all environment variables in *text* from *environment*.

    Example::

        >>> substitute("${HOME}/path/to/data", {"HOME": "/usr/people/john-doe"})

        /usr/people/john-doe/path/to/data

    :param text: String which can contain environment variable
        (e.g. "${PATH}/to/somewhere").

    :param environment: Mapping of environment variables with their respective
        values.

    :return: Resolved text string.

    """

    def _substitute(match):
        origin = match.group(0)
        name = next(item for item in match.groups() if item is not None)
        return environment.get(name, origin)

    return ENV_PATTERN.sub(_substitute, text)

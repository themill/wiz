# :coding: utf-8

from _version import __version__

from packaging.requirements import Requirement

import wiz.definition
import wiz.package
import wiz.graph
import wiz.symbol
import wiz.spawn


def fetch_definitions(paths, max_depth=None):
    """Return mapping from all definitions available under *paths*.

    Discover all available definitions under *paths*, searching recursively
    up to *max_depth*.

    A definition mapping should be in the form of::

        {
            "command": {
                "app": "my-package",
                ...
            },
            "package": {
                "my-package": {
                    "1.1.0": <Definition(identifier="test", version="1.1.0")>,
                    "1.0.0": <Definition(identifier="test", version="1.0.0")>,
                    "0.1.0": <Definition(identifier="test", version="0.1.0")>,
                    ...
                },
                ...
            }
        }

    """
    return wiz.definition.fetch(paths, max_depth=max_depth)


def resolve_context(requirements, definition_mapping, environ_mapping=None):
    """Return context mapping from *requirements*.

    The context should contain the resolved environment mapping, the
    resolved command mapping, and an ordered list of all serialized packages
    which constitute the resolved context.

    It should be in the form of::

        {
            "command": {
                "app": "AppExe"
                ...
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            },
            "packages": [
                {"identifier": "test1==1.1.0", "version": "1.1.0", ...},
                {"identifier": "test2==0.3.0", "version": "0.3.0", ...},
                ...
            ]
        }

    *requirements* should be a list of string indicating the environment version
    requested to build the environment (e.g. ["package >= 1.0.0, < 2"])

    *definition_mapping* is a mapping regrouping all available definitions
    available.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    requirements = map(Requirement, requirements)

    resolver = wiz.graph.Resolver(
        definition_mapping[wiz.symbol.PACKAGE_REQUEST_TYPE]
    )
    packages = resolver.compute_packages(requirements)

    _environ_mapping = wiz.package.initiate_environ(environ_mapping)
    context = wiz.package.extract_context(
        packages, environ_mapping=_environ_mapping
    )

    context["packages"] = packages
    return context


def resolve_environment(requirements, definition_mapping, environ_mapping=None):
    """Return environment mapping from *requirements*.

    An environment mapping should be in the form of::

        {
            "KEY1": "value1",
            "KEY2": "value2",
            ...
        }

    *requirements* should be a list of string indicating the environment version
    requested to build the environment (e.g. "package >= 1.0.0, < 2")

    *definition_mapping* is a mapping regrouping all available definitions
    available.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    context = resolve_context(requirements, definition_mapping, environ_mapping)
    return context.get("environ", {})


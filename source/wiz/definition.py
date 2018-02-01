# :coding: utf-8

import os
import json

import mlog

import wiz.symbol
import wiz.environment
import wiz.application
import wiz.exception


def fetch(paths, max_depth=None):
    """Return mapping from all environment definitions available under *paths*.

    :func:`discover` available environments under *paths*, searching recursively
    up to *max_depth*.

    """
    mapping = {
        wiz.symbol.APPLICATION_TYPE: {},
        wiz.symbol.ENVIRONMENT_TYPE: {}
    }

    for definition in discover(paths, max_depth=max_depth):
        if definition.type == wiz.symbol.ENVIRONMENT_TYPE:
            mapping[definition.type].setdefault(definition.identifier, [])
            mapping[definition.type][definition.identifier].append(definition)
        elif definition.type == wiz.symbol.APPLICATION_TYPE:
            mapping[definition.type][definition.identifier] = definition
    return mapping


def search(requirement, paths, max_depth=None):
    """Return mapping from environment definitions matching *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    :func:`~wiz.definition.discover` available environments under *paths*,
    searching recursively up to *max_depth*.

    """
    logger = mlog.Logger(__name__ + ".search")
    logger.info(
        "Search environment environment definitions matching '{}'"
        .format(requirement)
    )

    mapping = {
        wiz.symbol.APPLICATION_TYPE: {},
        wiz.symbol.ENVIRONMENT_TYPE: {}
    }

    for definition in discover(paths, max_depth=max_depth):
        if (
            requirement.name.lower() in definition.identifier.lower() or
            requirement.name.lower() in definition.description.lower()
        ):
            _type = definition.type
            if (
                _type == wiz.symbol.ENVIRONMENT_TYPE and
                definition.version in requirement.specifier
            ):
                mapping[_type].setdefault(definition.identifier, [])
                mapping[_type][definition.identifier].append(definition)

            elif _type == wiz.symbol.APPLICATION_TYPE:
                mapping[_type][definition.identifier] = definition

    return mapping


def discover(paths, max_depth=None):
    """Discover and yield all definitions found under *paths*.

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
        logger.debug("Searching under {!r} for definition files.".format(path))

        initial_depth = path.rstrip(os.sep).count(os.sep)
        for base, _, filenames in os.walk(path):
            depth = base.count(os.sep)
            if max_depth is not None and (depth - initial_depth) > max_depth:
                continue

            for filename in filenames:
                _, extension = os.path.splitext(filename)
                if extension != ".json":
                    continue

                definition_path = os.path.join(base, filename)
                logger.debug(
                    "Discovered definition file {!r}.".format(definition_path)
                )

                try:
                    definition = load(definition_path)
                    definition["registry"] = path
                except (
                    IOError, ValueError, TypeError,
                    wiz.exception.WizError
                ):
                    logger.warning(
                        "Error occurred trying to load definition "
                        "from {!r}".format(definition_path),
                        traceback=True
                    )
                    continue
                else:
                    logger.debug(
                        "Loaded definition {!r} from {!r}."
                        .format(definition.identifier, definition_path)
                    )
                    yield definition


def load(path):
    """Load and return :class:`Definition` from *path*."""
    with open(path, "r") as stream:
        definition_data = json.load(stream)

        # TODO: Validate with JSON-Schema.

        if definition_data.get("type") == wiz.symbol.ENVIRONMENT_TYPE:
            definition = wiz.environment.Environment(**definition_data)
            return definition

        elif definition_data.get("type") == wiz.symbol.APPLICATION_TYPE:
            definition = wiz.application.Application(**definition_data)
            return definition

        raise wiz.exception.IncorrectDefinition(
            "The definition type is incorrect: {}".format(
                definition_data.get("type")
            )
        )

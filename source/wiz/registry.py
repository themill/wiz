# :coding: utf-8

from __future__ import absolute_import
import os
import logging

import wiz.config
import wiz.exception
import wiz.filesystem
import wiz.utility


def get_local():
    """Return the local registry if available.

    :return: :file:`~/.wiz/registry` or None.

    """
    registry_path = os.path.join(os.path.expanduser("~"), ".wiz", "registry")
    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path


def get_defaults():
    """Return the default registries.

    :return: List of default registry paths.

    .. seealso:: :ref:`configuration/registry_paths`

    """
    config = wiz.config.fetch()
    return config.get("registry", {}).get("paths", [])


def fetch(paths, include_local=True, include_working_directory=True):
    """Fetch all registries from *paths*.

    :param paths: List of paths to consider as registry paths if available.

    :param include_local: Indicate whether the local registry should be
        included.

    :param include_working_directory: Indicate whether the current working
        directory should be parsed to discover registry folders.

    :return: List of valid registry paths.

    """
    registries = []

    for path in paths:
        path = os.path.abspath(path)

        if not wiz.filesystem.is_accessible(path):
            continue
        registries.append(path)

    if include_working_directory:
        for registry_path in discover(os.getcwd()):
            registries.append(registry_path)

    registry_path = get_local()
    if registry_path and include_local:
        registries.append(registry_path)

    return registries


def discover(path):
    """Yield available registry folders from *path* folder hierarchy.

    Each folder constituting the hierarchy of *path* are parsed so that
    existing :file:`.wiz/registry` folders can be yield from the deepest
    to the closest.

    Example::

        >>> list(discover("/jobs/ads/project/identity/shot"))
        [
            "/jobs/ads/project/.wiz/registry",
            "/jobs/ads/project/identity/shot/.wiz/registry"
        ]

    :param path: Path to discover registries from.

    :return: List of valid registry paths.

    .. seealso:: :ref:`registry/discover-implicit`

    """
    path = os.path.abspath(path)

    config = wiz.config.fetch()

    # Only discover the registry if the top level hierarchy is defined in the
    # config as 'discovery_prefix'.
    prefix = config.get("registry", {}).get("discovery_prefix", os.sep)
    if not path.startswith(prefix):
        return

    _path = [p for p in path[len(prefix):].split(os.sep) if len(p)]
    for folder in _path:
        prefix = os.path.join(prefix, folder)
        registry_path = os.path.join(prefix, ".wiz", "registry")

        if wiz.filesystem.is_accessible(registry_path):
            yield registry_path


def install_to_path(definitions, registry_path, overwrite=False):
    """Install a list of definitions to a registry on the file system.

    :param definitions: List of :class:`wiz.definition.Definition` instances.

    :param registry_path: Targeted registry path to install to

    :param overwrite: Indicate whether existing definitions in the target
        registry should be overwritten. Default is False.

    :raise: :exc:`wiz.exception.DefinitionsExist` if definitions already exist
        in the target registry and overwrite is False.

    :raise: :exc:`wiz.exception.InstallNoChanges` if definitions already exists
        in the target registry and no changes is detected.

    :raise: :exc:`wiz.exception.InstallError` if the target registry path is not
        a valid directory.

    :raise: :exc:`OSError` if definitions can not be exported in
        *registry_path*.

    """
    logger = logging.getLogger(__name__ + ".install_to_path")

    if not os.path.isdir(registry_path):
        raise wiz.exception.InstallError(
            "{!r} is not a valid registry directory.".format(registry_path)
        )

    registry_path = os.path.abspath(registry_path)

    # Record definitions to install.
    _definitions = []

    # Record existing definitions per identifier.
    existing = {}

    # Fetch all definitions from registry.
    mapping = wiz.fetch_definition_mapping([registry_path])

    for definition in definitions:
        request = definition.qualified_version_identifier

        try:
            _definition = wiz.fetch_definition(request, mapping)

        except wiz.exception.RequestNotFound:
            _definitions.append(definition)

        else:
            data1 = definition.data(copy_data=False)
            data2 = _definition.data(copy_data=False)
            if data1 == data2:
                continue

            existing[definition.qualified_identifier] = _definition
            _definitions.append(definition)

    # If no content was released.
    if len(_definitions) == 0:
        raise wiz.exception.InstallNoChanges()

    # Fail if overwrite is False and some definition paths exist in registry.
    if len(existing) > 0 and overwrite is False:
        raise wiz.exception.DefinitionsExist([
            wiz.utility.compute_label(definition)
            for definition in existing.values()
        ])

    # Release definitions
    for definition in _definitions:
        path = registry_path
        identifier = definition.identifier

        # Replace existing definition if necessary.
        if identifier in existing.keys():
            existing_definition_path = existing[identifier].path
            path = os.path.dirname(existing_definition_path)
            os.remove(existing_definition_path)

        wiz.export_definition(path, definition, overwrite=True)

    logger.info(
        "Successfully installed {number} definition(s) to "
        "registry {registry!r}.".format(
            number=len(_definitions),
            registry=registry_path
        )
    )

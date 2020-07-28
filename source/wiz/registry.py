# :coding: utf-8

import os

import wiz.exception
import wiz.filesystem
import wiz.logging
import wiz.utility


def get_local():
    """Return the local registry if available."""
    registry_path = os.path.join(os.path.expanduser("~"), ".wiz", "registry")
    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path


def fetch(paths, include_local=True, include_working_directory=True):
    """Fetch all registries from *paths*.

    *include_local* indicates whether the local registry should be included.

    *include_working_directory* indicates whether the current working directory
    should be parsed to discover registry folders.

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

    .. important::

        Registry folders can be discovered only under :file:`/jobs/ads`.

    """
    # TODO: The prefix should be set as an option in configuration file
    path = os.path.abspath(path)

    # Only discover the registry if the top level hierarchy is /jobs/ads.
    prefix = os.path.join(os.sep, "jobs", "ads")
    if not path.startswith(prefix):
        return

    for folder in path.split(os.sep)[3:]:
        prefix = os.path.join(prefix, folder)
        registry_path = os.path.join(prefix, ".wiz", "registry")

        if wiz.filesystem.is_accessible(registry_path):
            yield registry_path


def install_to_path(definitions, registry_path, overwrite=False):
    """Install a list of definitions to a registry on the file system.

    *definitions* must be a list of valid :class:`~wiz.definition.Definition`
    instances.

    *registry_path* is the target registry path to install to.

    If *overwrite* is True, any existing definitions in the target registry
    will be overwritten.

    Raises :exc:`wiz.exception.DefinitionsExist` if definitions already exist in
    the target registry and overwrite is False.

    Raises :exc:`wiz.exception.InstallNoChanges` if definitions already exists
    in the target registry and no changes is detected.

    Raises :exc:`wiz.exception.InstallError` if the target registry path is not
    a valid directory.

    Raises :exc:`OSError` if definitions can not be exported in *registry_path*.

    """
    logger = wiz.logging.Logger(__name__ + ".install_to_path")

    if not os.path.isdir(registry_path):
        raise wiz.exception.InstallError(
            "{!r} is not a valid registry directory.".format(registry_path)
        )

    registry_path = os.path.abspath(registry_path)
    if not registry_path.endswith(".wiz/registry"):
        registry_path = os.path.join(registry_path, ".wiz", "registry")

    # Record definitions to install.
    _definitions = []

    # Record existing definitions per identifier.
    existing_definition_map = {}

    # Fetch all definitions from registry.
    mapping = wiz.fetch_definition_mapping([registry_path])

    for definition in definitions:
        request = definition.qualified_version_identifier

        try:
            _definition = wiz.fetch_definition(request, mapping)

        except wiz.exception.RequestNotFound:
            _definitions.append(definition.sanitized())

        else:
            if definition.sanitized() == _definition.sanitized():
                continue

            existing_definition_map[definition.identifier] = _definition
            _definitions.append(definition.sanitized())

    # If no content was released.
    if len(_definitions) == 0:
        raise wiz.exception.InstallNoChanges()

    # Fail if overwrite is False and some definition paths exist in registry.
    if len(existing_definition_map) > 0 and overwrite is False:
        raise wiz.exception.DefinitionsExist([
            wiz.utility.compute_label(definition)
            for definition in existing_definition_map.values()
        ])

    # Release definitions
    for definition in _definitions:
        path = registry_path
        identifier = definition.identifier

        # Replace existing definition if necessary.
        if identifier in existing_definition_map.keys():
            existing_definition_path = (
                existing_definition_map[identifier].get("definition-location")
            )
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

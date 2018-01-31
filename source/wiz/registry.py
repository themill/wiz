# :coding: utf-8

import os


def get_local():
    """Return the local registry if available."""
    registry_path = os.path.join(
        os.path.expanduser("~"), ".wiz", "registry"
    )

    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path


def get_defaults():
    """Return the default registries."""
    return [
        os.path.join(os.sep, "mill3d", "server", "apps", "WIZ", "registry"),
        os.path.join(os.sep, "jobs", "ads", ".wiz", "registry")
    ]


def fetch(paths, include_local=True, include_working_directory=True):
    """Fetch all registries from *paths*.

    *include_local* indicate whether the local registry should be included.

    *include_local* indicate whether the current working directory should be
     parsed to discover a registry.

    """
    registries = []

    for path in paths:
        if not os.path.isdir(path) and not os.access(path, os.R_OK):
            continue
        registries.append(path)

    if include_working_directory:
        registry_path = discover(os.getcwd())
        if registry_path:
            registries.append(registry_path)

    registry_path = get_local()
    if registry_path and include_local:
        registries.append(registry_path)

    registries.reverse()
    return registries


def discover(path):
    """Return registry from *path* if available under the folder structure.

    The registry path should be a ".registry" folder within *path*.

    Return the registry path discovered, or None if the register is not found
    or not accessible.

    .. note::

        No registry will be fetched if *path* is not under `/jobs/ads`.

    """
    path = os.path.abspath(path)

    # Only discover the registry if the top level hierarchy is /jobs/ads.
    prefix = os.path.join(os.sep, "jobs", "ads")
    if not path.startswith(prefix):
        return

    registry_path = os.path.join(path, ".wiz", "registry")
    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path

# :coding: utf-8

import os

import wiz.filesystem


def get_local():
    """Return the local registry if available."""
    registry_path = os.path.join(os.path.expanduser("~"), ".wiz", "registry")
    if os.path.isdir(registry_path) and os.access(registry_path, os.R_OK):
        return registry_path


def get_defaults():
    """Return the default registries."""
    server_root = os.path.join(os.sep, "mill3d", "server", "apps", "WIZ")

    return [
        os.path.join(server_root, "registry", "primary", "default"),
        os.path.join(server_root, "registry", "secondary", "default"),
        os.path.join(os.sep, "jobs", ".common", "wiz", "registry")
    ]


def fetch(paths, include_local=True, include_working_directory=True):
    """Fetch all registries from *paths*.

    *include_local* indicates whether the local registry should be included.

    *include_working_directory* indicates whether the current working directory
    should be parsed to discover registry folders.

    """
    registries = []

    for path in paths:
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
    existing :file:`.common/wiz/registry` folders can be yield from the deepest
    to the closest.

    Example::

        >>> list(discover("/jobs/ads/project/identity/shot"))
        [
            "/jobs/ads/project/.common/wiz/registry",
            "/jobs/ads/project/identity/shot/.common/wiz/registry"
        ]

    .. important::

        Registry folders can be discovered only under :file:`/jobs/ads`.

    """
    path = os.path.abspath(path)

    # Only discover the registry if the top level hierarchy is /jobs/ads.
    prefix = os.path.join(os.sep, "jobs", "ads")
    if not path.startswith(prefix):
        return

    for folder in path.split(os.sep)[3:]:
        prefix = os.path.join(prefix, folder)
        registry_path = os.path.join(prefix, ".common", "wiz", "registry")

        if wiz.filesystem.is_accessible(registry_path):
            yield registry_path

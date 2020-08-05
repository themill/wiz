# :coding: utf-8

import collections
import imp
import os
import uuid

import toml

import wiz.logging
import wiz.utility

#: Global configuration mapping.
_CONFIG = None


def fetch(refresh=False):
    """Fetch configuration mapping.

    The configuration created is cached for future usage so that configuration
    previously fetched will be returned.

    If *refresh* is set to True, the configuration will be re-created.

    """
    logger = wiz.logging.Logger(__name__ + ".fetch")

    global _CONFIG

    if _CONFIG is not None and not refresh:
        return _CONFIG

    config = {}

    # Fetch all configurations paths.
    root = os.path.dirname(__file__)
    paths = [
        os.path.join(root, "package_data", "config.toml"),
        os.path.join(os.path.expanduser("~"), ".wiz", "config.toml")
    ]

    for file_path in paths:
        if not os.path.isfile(file_path):
            continue

        try:
            wiz.utility.deep_update(config, toml.load(file_path))
        except Exception as error:
            logger.warning(
                "Failed to load configuration from \"{0}\" [{1}]"
                .format(file_path, error)
            )

    # Extend configuration mapping with plugins
    for plugin in _discover_plugins():
        try:
            plugin.register(config)
        except Exception as error:
            logger.warning(
                "Failed to register plugin from \"{0}\" [{1}]"
                .format(plugin.__file__, error)
            )

    _CONFIG = config
    return _CONFIG


def _discover_plugins():
    """Discover and return plugins.
    """
    logger = wiz.logging.Logger(__name__ + "._discover_plugins")

    # Fetch all plugin paths.
    root = os.path.dirname(__file__)
    paths = [
        os.path.join(root, "package_data", "plugins"),
        os.path.join(os.path.expanduser("~"), ".wiz", "plugins")
    ]

    plugins = collections.OrderedDict()

    for dir_path in paths:
        if not os.path.isdir(dir_path):
            continue

        for file_path in os.listdir(dir_path):
            name, extension = os.path.splitext(file_path)
            if extension != ".py":
                continue

            module_path = os.path.join(dir_path, file_path)
            unique_name = uuid.uuid4().hex

            try:
                module = imp.load_source(unique_name, module_path)
                plugins[module.IDENTIFIER] = module

            except Exception as error:
                logger.warning(
                    "Failed to load plugin from \"{0}\" [{1}]"
                    .format(module_path, error)
                )
                continue

    return plugins.values()

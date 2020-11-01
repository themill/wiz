# :coding: utf-8

from __future__ import absolute_import
import collections
import imp
import os
import uuid
import logging

import toml

import wiz.utility

#: Global configuration mapping.
_CONFIG = None


def fetch(refresh=False):
    """Fetch configuration mapping.

    The configuration created is cached for future usage so that configuration
    previously fetched will be returned.

    :param refresh: Indicate whether the configuration should be re-created
        instead of using configuration previously created whenever possible.
        Default is False.

    :return: Configuration mapping.

    """
    logger = logging.getLogger(__name__ + ".fetch")

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

    :return: List of plugins discovered.

    """
    logger = logging.getLogger(__name__ + "._discover_plugins")

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

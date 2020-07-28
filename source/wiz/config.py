# :coding: utf-8

import imp
import os
import uuid

import toml

import wiz.logging

#: Path to default configuration file.
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "package_data", "config.toml"
)

#: Path to default plugin path.
DEFAULT_PLUGIN_PATH = os.path.join(
    os.path.dirname(__file__), "package_data", "plugins"
)


def fetch():
    """Fetch configuration mapping.
    """
    logger = wiz.logging.Logger(__name__ + ".fetch")

    path = os.environ.get("WIZ_CONFIG_PATH", DEFAULT_CONFIG_PATH)
    config = toml.load(path)

    # Extend configuration mapping with plugins
    for plugin in discover_plugins():
        try:
            plugin.register(config)
        except AttributeError:
            logger.warning(
                "Failed to register plugin from module: {0}"
                .format(plugin.__file__)
            )

    return toml.load(path)


def discover_plugins():
    """Discover and yield plugins.
    """
    logger = wiz.logging.Logger(__name__ + ".discover_plugins")

    paths = []

    environ_value = os.environ.get("WIZ_PLUGIN_PATHS")
    if environ_value:
        paths += environ_value.split(os.pathsep)

    # Add default plugin path.
    paths.append(DEFAULT_PLUGIN_PATH)

    # Process plugins in reversed to give priority to those defined first within
    # the environment variable value.
    for dir_path in reversed(paths):
        for file_path in os.listdir(dir_path):
            name, extension = os.path.splitext(file_path)
            if extension != ".py":
                continue

            module_path = os.path.join(dir_path, file_path)
            unique_name = uuid.uuid4().hex

            try:
                module = imp.load_source(unique_name, module_path)
            except Exception as error:
                logger.warning(
                    "Failed to load plugin from \"{0}\": {1}"
                    .format(module_path, error)
                )
                continue

            yield module

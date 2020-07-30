# :coding: utf-8

import wiz.registry

#: Unique identifier of the plugin.
IDENTIFIER = "installer"


def install_definitions(paths, registry_target, overwrite=False):
    """Install a definition file to a registry.

    *paths* is the path list to all definition files.

    *registry_target* should be a path to a local registry.

    If *overwrite* is True, any existing definitions in the target registry
    will be overwritten.

    Raises :exc:`wiz.exception.IncorrectDefinition` if data in *paths* cannot
    create a valid instance of :class:`wiz.definition.Definition`.

    Raises :exc:`wiz.exception.DefinitionExists` if definition already exists in
    the target registry and *overwrite* is False.

    Raises :exc:`OSError` if the definition can not be exported in a registry
    local *path*.

    """
    definitions = []

    for path in paths:
        _definition = wiz.load_definition(path)
        definitions.append(_definition)

    wiz.registry.install_to_path(
        definitions, registry_target, overwrite=overwrite
    )


def register(config):
    """Register definition installer callback."""
    config.setdefault("callback", {})
    config["callback"]["install"] = install_definitions

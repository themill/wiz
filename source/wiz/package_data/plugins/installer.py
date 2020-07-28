# :coding: utf-8

import wiz.registry


def register(config):
    """Register definition installer callback."""
    config.setdefault("callback", {})
    config["callback"]["install"] = wiz.registry.install_to_path

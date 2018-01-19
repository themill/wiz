# :coding: utf-8


import wiz.command_line


def test_resolve_valid_tree(registry):
    """Resolve an environment from a definition mapping."""
    wiz.command_line.main([
        "-v", "debug", "view", "envA", "envG", "--registries", registry]
    )

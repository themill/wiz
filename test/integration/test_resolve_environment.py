# :coding: utf-8


import umwelt.command_line


def test_resolve_valid_tree(registry):
    """Resolve an environment from a definition mapping."""
    umwelt.command_line.main([
        "-v", "debug", "view", "envA", "envG", "--registries", registry]
    )

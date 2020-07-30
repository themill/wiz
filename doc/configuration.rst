.. _configuration:

*******************
Using Configuration
*******************

Wiz configuration is fully customizable via :term:`TOML` configuration files
and plugins.

The following configuration file is used by default:

.. literalinclude:: ../source/wiz/package_data/config.toml
   :language: toml

It is possible to overwrite or add keywords to this configuration by defining
other configuration files using :envvar:`WIZ_CONFIG_PATHS`, or using adding a
personal configuration file.

.. important::

    The order of paths set in :envvar:`WIZ_CONFIG_PATHS` is used to define
    the priority in case of conflicts. The first path will have the highest
    priority and the last path will have the lowest priority.

    The personal configuration has always the highest priority over all other
    configurations.

Let's re-use the example from the :ref:`previous page <getting_started>`::

    >>> wiz -r ./registry list package

    Registries
    -----------------
    [0] /tmp/registry

    ...

Instead of having to constantly set the registry path in the command line, we
will initialize it by default in a personal configuration file.

Add the following configuration in :file:`~/.wiz/config.toml`::

    name = "Personal"

    [registry]
    paths=["/tmp/registry"]

We can now run the same command without indicating the registry path::

    >>> wiz list package

    Registries
    -----------------
    [0] /tmp/registry

    ...


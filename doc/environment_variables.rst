.. _environment_variables:

*********************
Environment variables
*********************

Environment variables directly defined or referenced by this package.

.. envvar:: WIZ_CONFIG_PATHS

    Path to :term:`TOML` configuration files to customize default
    values and callback. Multiple paths should be separated by
    :attr:`os.pathsep` (e.g. ':' or ';').

.. envvar:: WIZ_PLUGIN_PATHS

    Search paths for plugins to define the global configuration.
    Multiple paths should be separated by :attr:`os.pathsep` (e.g. ':' or ';').

.. envvar:: INSTALL_LOCATION

    Environment variable used within a Wiz definition environment to refer to
    the install location of a package.

    .. seealso:: :ref:`definition/install_location`

.. envvar:: INSTALL_ROOT

    Environment variable used within a Wiz definition environment to refer to
    the root of the install location of a package.

    .. seealso:: :ref:`definition/install_root`

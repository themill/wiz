.. _environment_variables:

*********************
Environment variables
*********************

Environment variables directly defined or referenced by this package.

.. envvar:: WIZ_CONFIG_PATH

    Path to to :term:`TOML` configuration file to use to initialize default
    values and callback. A reasonable default will be provided if this
    environment variable is not set.

.. envvar:: WIZ_PLUGIN_PATHS

    Paths to search for plugins to load and use to define the global
    configuration mapping. Multiple paths can be specified by separating with
    the value of :attr:`os.pathsep` (e.g. ':' or ';').

.. envvar:: INSTALL_LOCATION

    Environment variable used within a Wiz definition environment to refer to
    the install location of a package.

    .. seealso:: :ref:`definition/install_location`

.. envvar:: INSTALL_ROOT

    Environment variable used within a Wiz definition environment to refer to
    the root of the install location of a package.

    .. seealso:: :ref:`definition/install_root`

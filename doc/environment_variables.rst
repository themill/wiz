.. _environment_variables:

*********************
Environment variables
*********************

Environment variables directly defined or referenced by this package.

.. envvar:: INSTALL_LOCATION

    Environment variable used inside a Wiz definition environment to refer to
    the install location of a package.
    At resolve time, Wiz will substitude the environment variable with the
    'install-location' defined in the same definition.

    .. code-block:: python

        {
            "identifier: "test"
            "environ": {
                "PATH": "${INSTALL_LOCATION}/bin:{PATH}",
            "install-location": "/path/to/test"
        }

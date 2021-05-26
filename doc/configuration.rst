.. _configuration:

*******************
Using Configuration
*******************

.. highlight:: shell

The Wiz configuration is fully customizable via :term:`TOML` configuration files
and :ref:`plugins <plugins>`.

The following configuration file is used by default:

.. literalinclude:: ../source/wiz/package_data/config.toml
   :language: toml

It is possible to overwrite, extend or add keywords to this configuration by
adding a personal configuration file in :file:`~/.wiz/config.toml`. The default
configuration will always be loaded first, followed by the personal
configuration.

.. important::

    The default configuration will be recursively updated by the personal
    configuration.

You can fetch the configuration via the :term:`Python` API with
:func:`wiz.config.fetch`:

.. code-block:: python

    >>> wiz.config.fetch()

Let's go through a few usage examples.

.. _configuration/registry_paths:

Registry paths
--------------

In :ref:`Getting Started <getting_started>`, we used the :option:`wiz -r`
option to indicate the registry path to use::

    >>> wiz -r /tmp/registry list package

    Registries
    -----------------
    [0] /tmp/registry

    ...

Instead of having to constantly set the registry path in the command line, we
will add the following configuration in :file:`~/.wiz/config.toml`:

.. code-block:: toml

    [registry]
    paths=["/tmp/registry"]

It is now possible to run the same command without indicating the registry
path::

    >>> wiz list package

    Registries
    -----------------
    [0] /tmp/registry

    ...

.. hint::

    It is highly recommended to define custom registry paths when
    :ref:`installing <installing/source/options>` the package instead of
    defining it for each user as it can be error prone.

.. _configuration/initial_environment:

Initial environment
-------------------

The resolved environment will not take any external environment variables into
account as the goal is to create a deterministic environment. However, it is
sometimes required to access external environment variables for an application
to execute properly.

We can define a list of environment variables which should always get
transferred to a resolved environment by adding the following configuration in
:file:`~/.wiz/config.toml`:

.. code-block:: toml

    [environ]
    passthrough=["ENVIRON_TEST1"]

Using the "python" definition created in a :ref:`previous example
<getting_started>`, we can ensure that this variable is properly transferred to
the resolved environment::

    >>> export ENVIRON_TEST1=1
    >>> export ENVIRON_TEST2=1
    >>> wiz -r /tmp/registry use python
    info: Spawn shell: /bin/bash

    >>> echo $ENVIRON_TEST1
    1
    >>> echo $ENVIRON_TEST2 // Empty

It is also possible to define initial environment variables by modifying the
configuration file as follows:

.. code-block:: toml

    [environ]
    initial={ENVIRON_TEST3 = "VALUE"}
    passthrough=["ENVIRON_TEST1"]

Ensure that it is properly propagated to the resolved environment::

    >>> wiz -r /tmp/registry use python
    info: Spawn shell: /bin/bash

    >>> echo $ENVIRON_TEST3
    VALUE

.. hint::

    If you are defining a lot of initial environment variables in the
    configuration, using :term:`TOML`'s inline table will become cumbersome and
    you will probably prefer this notation:

    .. code-block:: toml

        [environ.initial]
        ENVIRON_TEST1=VALUE1
        ENVIRON_TEST2=VALUE2
        ENVIRON_TEST3=VALUE3
        ENVIRON_TEST4=VALUE4

See :ref:`here <plugins>` how to initialize environment variables using plugins.

.. warning::

    Initial variables will get overwritten or extended by the resolved
    environment if a :ref:`package definition <definition>` is defining the same
    environment variables.

.. hint::

    It is highly recommended to define initial environment variables when
    :ref:`installing <installing/source/options>` the package instead of
    defining it for each user as it can be error prone.

.. _configuration/logging:

Customize Logging
-----------------

By default, :data:`wiz.logging.DEFAULT_CONFIG` will be used to initialize
the Python logging for the command line tool with two handlers:

* The 'console' handler is a :class:`~logging.StreamHandler` instance which
  handles terminal output. It is using :class:`~coloredlogs.ColoredFormatter` to
  display messages with a color corresponding to the level used.

* The 'file' handler is a :class:`~logging.handlers.RotatingFileHandler`
  instance which saves detailed logs on the disk for each user.

The configuration can be used to modify these handlers, or add new ones. For
instance, the following configuration will disable the 'file' handler and add a
timestamp to each messages displayed via the 'console' handler:

.. code-block:: toml

    [logging.root]
    handlers=["console"]

    [logging.formatters.standard]
    format="%(asctime)s - %(message)s"

.. note::

    Logging configuration should adhere to the
    :ref:`Configuration dictionary schema <logging-config-dictschema>`.

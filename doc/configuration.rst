.. _configuration:

*******************
Using Configuration
*******************

.. highlight:: shell

Wiz configuration is fully customizable via :term:`TOML` configuration files
and :ref:`plugins <plugins>`.

The following configuration file is used by default:

.. literalinclude:: ../source/wiz/package_data/config.toml
   :language: toml

It is possible to overwrite, extend or add keywords to this configuration by
defining other configuration files using :envvar:`WIZ_CONFIG_PATHS`, or adding a
personal configuration file in :file:`~/.wiz/config.toml`.

The default configuration will always be loaded first, followed by the
configurations defined by :envvar:`WIZ_CONFIG_PATHS` in reversed order. The
personal configuration is always loaded last.

.. important::

    If a non-mutable keyword values is defined in two configuration files, the
    configuration loaded last will overwrite the keyword. For mutable keyword
    values (dictionaries and lists), the configuration loaded last will extend
    the previous value.

You can fetch the configuration via the :term:`Python` API with
:func:`wiz.config.fetch`:

.. code-block:: python

    >>> wiz.config.fetch()

Let's go through a few examples of usage.

.. _configuration/setup:

Setup
-----

Let's first define a custom configuration file in the temporary folder using
:envvar:`WIZ_CONFIG_PATHS`::

    >>> export WIZ_CONFIG_PATHS="/tmp/config.toml"

Now add the following configuration in :file:`/tmp/config.toml`::

    name = "Custom"

.. _configuration/registry_paths:

Registry paths
--------------

In the :ref:`previous page <getting_started>`, we used the :option:`wiz -r`
option to indicate the registry path to use::

    >>> wiz -r /tmp/registry list package

    Registries
    -----------------
    [0] /tmp/registry

    ...

Instead of having to constantly set the registry path in the command line, we
will use the configuration file :ref:`previously created <configuration/setup>`
to initialize this value:

.. code-block:: toml

    name = "Custom"

    [registry]
    paths=["/tmp/registry"]

It is now possible to run the same command without indicating the registry
path::

    >>> wiz list package

    Registries
    -----------------
    [0] /tmp/registry

    ...

Let's now define another registry within a personal configuration file in
:file:`~/.wiz/config.toml`:

.. code-block:: toml

    name = "Personal"

    [registry]
    paths=["/tmp/another_registry"]

Let's create the registry to ensure that it can be used::

    >>> mkdir /tmp/another_registry

Now the new registry is added to the registry list::

    >>> wiz list package

    Registries
    -----------------
    [0] /tmp/registry
    [1] /tmp/another_registry

    ...

.. _configuration/initial_environment:

Initial environment
-------------------

The resolved environment will not take any external environment variables into
account as the goal is to create a deterministic environment. However, it is
sometimes required to access external environment variables for an application
to execute properly.

We can define a list of environment variables which should always get
transferred to a resolved environment by using the configuration file
:ref:`previously created <configuration/setup>`:

.. code-block:: toml

    name = "Custom"

    [environ]
    passthrough=["ENVIRON_TEST1"]

Using a definition created in a :ref:`previous example <getting_started>`, we
can ensure that this variable is properly transferred to the resolved
environment::

    >>> export ENVIRON_TEST1=1
    >>> export ENVIRON_TEST2=1
    >>> wiz -r /tmp/registry use python
    info: Spawn shell: /bin/bash

    >>> echo $ENVIRON_TEST1
    1
    >>> echo $ENVIRON_TEST2 // Empty

It is also possible to define initial environment variable by modifying the
configuration file as follows:

.. code-block:: toml

    name = "Custom"

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

        name = "Custom"

        [environ.initial]
        ENVIRON_TEST1=VALUE1
        ENVIRON_TEST2=VALUE2
        ENVIRON_TEST3=VALUE3
        ENVIRON_TEST4=VALUE4

We will see later how to initialize environment variable using :ref:`plugins
<plugins>`.

.. warning::

    Initial variables will get overwritten or extended by the resolved
    environment if a :ref:`package definition <definition>` is defining the same
    environment variables.

.. _definition:

*************************
Using Package Definitions
*************************

A package is defined as a collection of common commands and environment
variables. The package definition is a :term:`JSON` file.

Here is an example of package definition:

.. code-block:: json

    {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "Foo Application.",
        "system": {
            "os": "el >= 7, <8",
            "arch": "x86_64"
        },
        "command": {
            "app": "App0.1",
            "app-py": "AppPython"
        },
        "environ": {
            "LICENSE": "42000@licence.themill.com",
            "PATH": "/path/to/application:${PATH}",
            "PYTHONPATH": "/path/to/application/python:${PYTHONPATH}",
            "LD_LIBRARY_PATH": "/path/to/application:${LD_LIBRARY_PATH}"
        },
        "requirements": [
            "python > 2.7, < 3"
        ]
    }

.. seealso::

    Follow these :ref:`Guidelines <guidelines/package_definitions>` for
    writing proper package definitions.

.. _definition/identifier:

Identifier
----------

At minimum a package definition contains an ``identifier``, which has to be
unique. If an identifier is found in multiple :ref:`registries <registry>`, the
last sourced registry will define the package.

.. code-block:: json

    {
        "identifier": "maya"
    }

.. _definition/version:

Version
-------

The optional ``version`` keyword eases the package selection when a specific
range of version is required.

.. code-block:: json

    {
        "version": "0.1.0"
    }

The same version specifiers defined in :term:`PEP 440` are used::

    >>> wiz use "app-package >=0.1.0, <2"

The version could also be specified when running a command directly::

    >>> wiz run "app == 0.1.*"

.. seealso:: :ref:`definition/command`

If no version is requested, the latest version is automatically fetched.

.. _definition/description:

Description
-----------

An optional package ``description``.

.. code-block:: json

    {
        "description": "Foo Application."
    }

It is useful when searching for packages using::

    >>> wiz search app

.. _definition/system:

System
------

An optional ``system`` keyword can be used to limit the scope of a package
definition to a particular:

* Platform (e.g. Linux, Windows)
* Architecture (e.g. x86_64, i386)
* Operating System (e.g. CentOS 7.3, CentOS 6.5, MacOS, Windows)

.. code-block:: json

    {
        "system": {
            "platform": "linux",
            "os": "el >= 7, < 8",
            "arch": "x86_64"
        }
    }

The version specifiers defined :term:`PEP 440` are used to identify the
operating system version.

If no system keyword is provided, the definition could be fetched and loaded
from any platform.

.. _definition/environ:

Environment
-----------

The optional ``environ`` keyword defines the environment mapping.

The resolved environment combines all `environment variable mappings` from
all package definitions required to form the resolved context.

In order to combine two environment mappings, each variable value can be
augmented by referencing any variable names already included in the resolved
mapping.

If a variable value does not reference its variable name within its value, it
can override any precedent value.

.. code-block:: json

    {
        "environ": {
            "LICENSE": "42000@licence.themill.com",
            "PATH": "/path/to/application:${PATH}",
            "PYTHONPATH": "/path/to/application/python:${PYTHONPATH}",
            "LD_LIBRARY_PATH": "/path/to/application:${LD_LIBRARY_PATH}"
        }
    }

.. note::

    To help debug any accidental overwrites, a warning is being displayed each
    time a variable is overwriting another one.

.. _definition/command:

Commands
--------

The optional ``command`` keyword contains a mapping of commands that serves as
aliases when running within the resolved context.

.. code-block:: json

    {
        "command": {
            "nuke": "Nuke11.1",
            "nukex": "Nuke11.1 --nukex",
            "studio": "Nuke11.1 --studio",
            "hiero": "Nuke11.1 --hiero"
        }
    }

It can be used to run a command within a resolved environment (with or without
additional arguments):

.. code-block:: console

    >>> wiz use nuke plugin-nuke -- nukex
    >>> wiz use nuke plugin-nuke -- hiero
    >>> wiz use nuke plugin-nuke -- nuke /path/to/script

The command mappings are parsed when the package definitions are discovered so
that each command is associated with the definition package it is in. This
let the user call the command directly with the ``run`` command:

.. code-block:: console

    >>> wiz run nuke
    >>> wiz run nuke==10.5.*
    >>> wiz run nukex -- /path/to/script

.. warning::

    Each command must be unique within a :ref:`registry` and could be
    overwritten by another package definition in another registry.

.. _definition/requirements:

Requirements
------------

A optional ``requirements`` keyword can be used to reference other package
definitions. This indicates that the resulting context has to be composed of
other package definitions and thereby eases the creation of reliable context.

By default, the latest versions of definitions will be fetched, but specific
versions can be required. The same version specifiers defined in :term:`PEP 440`
are use:

.. code-block:: json

    {
        "requirements": [
            "python > 2.7, < 3"
        ]
    }

When several requirements are specified, the order will define the priority of
each required package definition. In case of conflict, the first requirement
will have priority over the latest.

.. warning::

    A definition and its requirements would be resolved into one context with a
    common environment variable mapping. Therefore it would not be safe to mix
    several DCCs into one context to prevent clashes::

        "requirement": [
            "nuke",
            "maya"
        ]

.. _definition/variants:

Variants
--------

When different environment mappings are available for one definition version, an
optional ``variants`` keyword can be used in order to define an array of
sub-definitions:

.. code-block:: json

    {
        "variant": [
            {
                "identifier": "variant1",
                "environ": {
                    "KEY": "A_VALUE"
                },
                "requirements": [
                    "env >= 1, < 2"
                ]
            },
            {
                "identifier": "variant2",
                "environ": {
                    "KEY": "ANOTHER_VALUE"
                },
                "requirements": [
                    "env >= 2, < 3"
                ]
            }
        ]
    }

The ``environ`` and ``requirements`` value will be combined with the global
``environ`` and ``requirements`` values if necessary.

By default the first variant that leads to a resolution of the graph will be
returned. However, a variant can also be requested individually::

    >>> wiz use foo[variant1]

.. _definition:

*******************
Package Definitions
*******************

.. _definition/package:

Introducing package definitions
===============================

A package definition is a :term:`JSON` file.

Here is an example definition:

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

.. note::

    Ideally a Meta-Schema would be used to validate the definition, which
    has not been implemented yet.

Identifier
----------

At minimum a package definition contains an ``identifier``, which has to be
unique.
If an identifier is found in multiple registries, the last sourced registry
will define the package.

.. code-block:: json

    {
        "identifier": "maya"
    }

Environment
-----------

The optional ``environ`` keyword defines the environment mapping.

The resolved environment combines all `environment variable mappings` from
the ordered definitions to create the final environment mapping.

In order to combine two environment mapping, each variable value can be
augmented by referencing any variable names already included in the resolved
mapping.

If a variable value does not reference its variable name within its value, it
can override any precedent value. To help debug any accidental overriding, a
warning should be displayed each time a variable is overriding another one.

.. code-block:: json

    {
        "environ": {
            "LICENSE": "42000@licence.themill.com",
            "PATH": "/path/to/application:${PATH}",
            "PYTHONPATH": "/path/to/application/python:${PYTHONPATH}",
            "LD_LIBRARY_PATH": "/path/to/application:${LD_LIBRARY_PATH}"
        }
    }

Version
-------

The optional ``version`` keyword eases the package selection when a specific
range of version is required.

.. code-block:: json

    {
        "version": "0.1.0"
    }

The same version specifiers defined in PEP 440 for Python should be used::

    >>> wiz use "app-package >=0.1.0, <2"

The version could also be specified when running a command directly::

    >>> wiz run "app >= 0.1.0, <2"

If no version is requested, the latest version is automatically fetched.

Description
-----------

An optional package ``description``.

.. code-block:: json

    {
        "description": "Foo Application."
    }

It is useful when searching for packages using::

    >>> wiz search app

System
------

An optional ``system`` keyword can be used to limit the scope of a package
definition to a particular:

* Platform (e.g. Linux, Windows)
* Architecture (e.g. x86_64, i386)
* Operating System (e.g. CentOS 7.3, CentOS 6.5, MacOS, Windows)

The version specifiers defined in PEP 440 should be used to identify the
operating system version.

If no system keyword is provided, the definition could be fetched and loaded
from any platform.

.. code-block:: json

    {
        "system": {
            "platform": "linux",
            "os": "el >= 7, < 8",
            "arch": "x86_64"
        }
    }

Requirements
------------

A optional ``requirements`` keyword can be used to reference other package
definitions. This indicates that the resulting context has to be composed of
other package definitions and thereby eases the creation of reliable context.

By default, the latest versions of definitions will be fetched, but specific
versions can be required.
It is possible to use the same version specifiers defined in PEP 440 for Python
in order to ease the dependency requirement:

.. code-block:: json

    {
        "requirements": [
            "python > 2.7, < 3"
        ]
    }

.. warning::

    A definition and its requirements would be resolved into one context with a
    common environment variable mapping. Therefore it would not be safe to mix
    several DCCs into one context to prevent clashes::

        "requirement": [
            "nuke",
            "maya"
        ]

Commands
--------

The optional ``command`` keyword contains a mapping of command that serves as
aliases when running within the resolved context.

.. code-block:: json

    {
        "command": {
            "app": "App0.1",
            "app-py": "AppPython"
        }
    }

.. seealso::

    :ref:`definition/commands`

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

.. _definition/commands:

Introducing Commands
====================
By including command aliases mapping within package definitions, it is possible
to simplify the user experience within the resolved context:

.. code-block:: json

    {
        "nuke": "Nuke11.1",
        "nukex": "Nuke11.1 --nukex",
        "studio": "Nuke11.1 --studio",
        "hiero": "Nuke11.1 --hiero",
    }

Without adding these command aliases to the definitions DCCs would have to be
launched using the executables name in the PATH, i.e:

.. code-block:: console

    >>> wiz use nuke
    >>> Nuke11.1

Adding the command aliases to the definitions simplifies the call to:

.. code-block:: console

    >>> wiz use nuke
    >>> nuke

.. warning::

    The command is being identified by the mapping keys and can be overwritten by
    another package definition in another registry.

.. rubric:: run

To further improve the user experience, it is be more practical to directly run
the command within the resolve context:

.. code-block:: console

    >>> wiz run nukex --from nuke-package

.. note::

    If additional arguments need to be passed to the command, the parsing process
    could become cumbersome. Quotes would be needed recognize the entire command
    as a value:

    >>> wiz run "nukex -V2 -x /path/to/script" --from nuke-package

Guidelines
==========
Here are some guidelines to write package definitions:

.. toctree::
    :maxdepth: 1

    guidelines

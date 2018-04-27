.. _guidelines:

**********
Guidelines
**********

.. _guidelines/package_definitions:

Package Definitions
===================

This is a list of things to do or avoid when creating package definitions.

Internal Environment Variables
------------------------------

Avoid setting environment variables in the same package definition they are
used in.

.. code-block:: json
    :icon: image/prefer.png

    {
        "environ": {
            "SIDEFX_ROOT": "/mill3d/server/apps/SIDEFX",
            "HFS_LOCATION": "/mill3d/server/apps/SIDEFX/linux-x86-64"
        }
    }

.. code-block:: json
    :icon: image/avoid.png

    {
        "environ": {
            "SIDEFX_ROOT": "/mill3d/server/apps/SIDEFX",
            "HFS_LOCATION": "{SIDEFX_ROOT}/linux-x86-64"
        }
    }


The environment variable substitution does not loop (to increase performance).
Therefore any environment variables that are set in the same definition they
are supposed to be substituted in will fail to substitute.

Order of Variant Resolve
------------------------

Avoid setting environment variables in a variant and using them in a the same
definition.

.. code-block:: json
    :icon: image/prefer.png

    {
        "environ": {
            "LICENSE": "42000@licence.themill.com"
        },
        "variants": [
            {
                "identifier": "2016",
                "environ": {
                    "PATH": "${MAYA_PLUGINS}/app/0.1.0/bin:${PATH}"
                }
            }
        ]
    }

.. code-block:: json
    :icon: image/avoid.png

    {
        "environ": {
            "LICENSE": "42000@licence.themill.com",
            "PATH": "${APP_PATH}/bin:${PATH}"
        },
        "variants": [
            {
                "identifier": "2016",
                "environ": {
                    "APP_PATH": "${MAYA_PLUGINS}/app/0.1.0",
                }
            }
        ]
    }

It is possible to set certain variables for the entire package definition and
others only for a variant, but they do not resolve inside the same
definition.

Versions
--------

When creating new versions for an application/plugin/library (i.e. "maya 2018"
vs "maya 2016" or "mtoa-2.1.0" vs "mtoa-2.1.0.1"), create a new package
definition file and use the ``version`` keyword.

Avoid using ``variants`` for versioning.

.. code-block:: json
    :icon: image/prefer.png

    {
        "identifier": "maya",
        "version": "2018"
    }

.. code-block:: json
    :icon: image/avoid.png

    {
        "identifier": "maya",
        "variants": [
            {
                "identifier": "2018"
            }
        ]
    }

Variants should be used only if a different requirement would have to change
the environment set.


.. code-block:: json
    :icon: image/prefer.png

    {
        "identifier": "mtoa",
        "version": "2.1.0",
        "variants": [
            {
                "identifier": "2018",
                "environ": {
                    "key": "value1"
                },
                "requirements": [
                    "maya >= 2018 ,< 2019"
                ]
            },
            {
                "identifier": "2016",
                "environ": {
                    "key": "value2"
                },
                "requirements": [
                    "maya >= 2016 ,< 2017"
                ]
            }
        ]
    }

.. code-block:: json
    :icon: image/avoid.png

    {
        "identifier": "mtoa-2018",
        "version": "2.1.0",
        "environ": {
            "key": "value"
        },
        "requirements": [
            "maya >= 2018 ,< 2019"
        ]
    }

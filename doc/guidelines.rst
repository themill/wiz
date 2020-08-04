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

.. extended-code-block:: json
    :icon: image/prefer.png

    {
        "environ": {
            "SIDEFX_ROOT": "/apps/SIDEFX",
            "HFS_LOCATION": "/apps/SIDEFX/linux-x86-64"
        }
    }

.. extended-code-block:: json
    :icon: image/avoid.png

    {
        "environ": {
            "SIDEFX_ROOT": "/apps/SIDEFX",
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

.. extended-code-block:: json
    :icon: image/prefer.png

    {
        "environ": {
            "LICENSE": "42000@licence.com"
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

.. extended-code-block:: json
    :icon: image/avoid.png

    {
        "environ": {
            "LICENSE": "42000@licence.com",
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

Version vs Variant
------------------

When creating new versions for a package (i.e. "maya-2018" and "maya-2016",
"mtoa-2.1.0" and "mtoa-2.1.0.1"), a new package definition file should be
created. The new version should not be part of the ``identifier``, but instead
the ``version`` keyword should be used.

Avoid using ``variants`` for versioning. Variants can be very expensive for the
performance of the graph resolution process.

.. extended-code-block:: json
    :icon: image/prefer.png

    {
        "identifier": "maya",
        "version": "2018"
    }

.. extended-code-block:: json
    :icon: image/avoid.png

    {
        "identifier": "maya-2018"
    }

.. extended-code-block:: json
    :icon: image/avoid.png

    {
        "identifier": "maya",
        "variants": [
            {
                "identifier": "2018"
            },
            {
                "identifier": "2016"
            }
        ]
    }

Variants should be used only if a different requirement would have to change
the environment set within a single package version.

.. extended-code-block:: json
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

.. extended-code-block:: json
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

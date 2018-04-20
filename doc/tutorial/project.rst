
Certain environment variables are currently set in a Job and affect DCC plugins
being loaded inside that environment.

.. _tutorial/project:

Project Configurations and Overrides
------------------------------------

To override certain package definitions in a job, a job registry needs to be
created.

So first, create a ``.wiz/registry`` directory in the job / shot / project.

Inside that registry certain project specific variables can be set with a
project package definition. Create a ``project.json`` package definition and
add the projects environment:

.. code-block:: console

    >>> cd .wiz/registry
    >>> vim project.json
    {
        "identifier": "my-project",
        "description": "Maya Application for my-project.",
        "environ": {
            "MILL_EPISODE_PATH": "/jobs/ads/{PROJECT}",
            "TDSVN_ROOT": "/jobs/ads/{PROJECT}/.common/3d"
        }
    }

Next the package definition including the command to override can be added.
Create a ``maya.json`` package definition and add the special environment:

.. code-block:: console

    >>> cd .wiz/registry
    >>> vim maya.json
    {
        "identifier": "my-project-maya",
        "description": "Maya Application for my-project.",
        "command": {
            "maya": "maya2018"
        },
        "environ": {
            "PYTHONPATH": "${TDSVN_ROOT}/library/python:${PYTHONPATH}",
            "MAYA_MODULE_PATH": "${TDSVN_ROOT}/maya/modules:${TDSVN_ROOT}/maya/modules/2018:${MAYA_MODULE_PATH}",
            "MAYA_SCRIPT_PATH": "${TDSVN_ROOT}/maya/scripts:${MAYA_SCRIPT_PATH}"
        },
        "requirements": [
            "my-project",
            "mill-maya"
        ]
    }

This custom job :term:`Maya` configuration can now be launched like:

.. code-block:: console

    >>> wiz run maya

.. note::

    Adjusting the requirements inside the job package definition can also add
    or remove certain plugins from the :term:`Maya` environment. Instead of
    ``mill-maya`` (includes all the default plugins), the requirement could be::

        "requirements": [
            "my-project",
            "maya",
            "mtoa == 2.1.0"
        ]

    Which would then just load the project configuration with a vanilla Maya
    setup and `mtoa`.

.. warning::

    Currently for the job registry to be picked up, the user needs to be in the
    directory the ``.wiz/registry`` is located. A hierarchical search for
    higher level registries for jobs is coming soon.

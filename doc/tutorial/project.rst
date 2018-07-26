Some environment variables should be set for a Job only so that DCC plugins or
applications would be affected only inside this environment.

.. _tutorial/project:

Project Configurations and Overrides
------------------------------------

Let's consider a fake project called ``my_project`` which can be replace with
any existing projects::

    /jobs/ads/my_project/

Create a :file:`.wiz/registry` directory in the project folder:

.. code-block:: console

    >>> mkdir -p /jobs/ads/my_project/.wiz/registry

Create a :file:`project.json` package definition file to indicate the
environment variables needed for the project:

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/project.json
    {
        "identifier": "my-project",
        "description": "Environment for my-project.",
        "environ": {
            "MILL_EPISODE_PATH": "/jobs/ads/my_project",
        }
    }

Create an additional :file:`td-svn.json` package definition file to indicate the
location of the TD SVN root folder within the project:

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/td-svn.json
    {
        "identifier": "td-svn",
        "description": "Environment for TD SVN.",
        "environ": {
            "TDSVN_ROOT": "${MILL_EPISODE_PATH}/.common/3d"
        },
        "requirements": [
            "my-project"
        ]
    }

Finally, a :file:`maya.json` could be added in order to override the `maya`
command so that the additional scripts and modules are included:

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/maya.json
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
            "td-svn",
            "mill-maya",
        ]
    }

.. note::

    The package identifier must be unique as the objective is to override the
    command and not the full `mill-maya` package which is needed as a
    requirement.

It is now possible to start :term:`Maya` anywhere under the project folder to
include all TD SVN scripts and modules.

.. code-block:: console

    >>> cd /jobs/ads/my_project
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

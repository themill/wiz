Some environment variables should be set for a Job only so that DCC plugins or
applications would be affected only inside this environment.

.. _tutorial/project:

Project Configurations and Overrides
------------------------------------

Let's consider a fake project called ``my_project`` which can be replaced with
any existing projects::

    /jobs/ads/my_project/

.. note::

    In order to use Wiz, :ref:`registries <registry/project>` need to exist in
    each level of the job hierarchy. A tool called :term:`Chore` has been
    developed to create that registry structure and fill it with definitions
    containing job environment variables (similar to what :term:`mill_cd`
    returns).

Going forward, we will assume that the registry structure and the environment
variable definitions exists.

Let's set up :term:`Maya` for this job using Maya 2016 and adding the
:term:`TD SVN` as an example.

Create a :file:`tdsvn.json` package definition file to indicate the
location of the :term:`TD SVN` root folder within the project:

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/tdsvn.json
    {
        "identifier": "tdsvn",
        "description": "Environment for TD SVN.",
        "environ": {
            "PYTHONPATH": "${INSTALL_LOCATION}/library/python:${PYTHONPATH}",
            "MAYA_MODULE_PATH": "${INSTALL_LOCATION}/maya/modules:${MAYA_MODULE_PATH}",
            "MAYA_SCRIPT_PATH": "${INSTALL_LOCATION}/maya/scripts:${MAYA_SCRIPT_PATH}",
            "TDSVN_ROOT": "${INSTALL_LOCATION}"
        },
        "requirements": [
            "job"
        ],
        "install-location": "${MILL_EPISODE_PATH}/.common/3d"
    }

Additionally, create a :file:`project-maya.json` package definition file to set the
desired :term:`Maya` version and :term:`TD SVN` requirement.

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/project.json
    {
        "identifier": "project",
        "namespace": "maya",
        "description": "Project Setup for Maya.",
        "auto-use": true,
        "conditions": [
            "maya"
        ],
        "requirements": [
            "maya == 2016.*",
            "td-svn"
        ]
    }


Let's break down this :file:`project-maya.json` package definition:

* The :ref:`namespace <definition/namespace>` keyword helps identifying the
  package, allowing similar definitions to be created for :term:`DCCs <DCC>`
  like :term:`Houdini` or :term:`Nuke`.

* The :ref:`auto-use <definition/auto-use>` keyword ensures that the package
  will always be added to the graph when this registry is included.

* The :ref:`conditions <definition/conditions>` keyword ensures that this
  definition is only being considered if 'maya' is part of the requests.

* The :ref:`requirements <definition/requirements>` keyword ensures that any
  requests for 'maya' will be constraint to a maya version of 2016.* and the
  "tdsvn" package is being added to the graph.


It is now possible to start :term:`Maya` anywhere under the project folder to
include all :term:`TD SVN` scripts and modules.

.. code-block:: console

    >>> cd /jobs/ads/my_project
    >>> wiz run maya

.. hint::

    Which definitions were used to create the environment :term:`Maya` launches
    in can be viewed like::

        >>> wiz use maya --view

        Registries
        ------------------------------------------------------
        [0] /mill3d/server/apps/WIZ/registry/primary/default
        [1] /mill3d/server/apps/WIZ/registry/secondary/default
        [2] /jobs/.wiz/registry/default
        [3] /jobs/ads/my_project/.wiz/registry


        Package         Version   Registry   Description
        -------------   -------   --------   ------------------------------------------------
        base-maya       unknown   0          Base environment variables for Maya Application.
        site            unknown   2          Current Mill site.
        maya            2016      0          Maya Application.
        job             unknown   3          Project Job setup.
        tdsvn           unknown   3          Environment for TD SVN.
        maya::project   unknown   3          Project Setup for Maya.

    In addition to the environment variables set, ``--view`` displays all
    definitions resolved and which registries they were found in.

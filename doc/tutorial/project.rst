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
            "MAYA_SCRIPT_PATH": "${INSTALL_LOCATION}/maya/scripts:${MAYA_SCRIPT_PATH}"
        },
        "requirements": [
            "job"
        ],
        "install-location": "${MILL_EPISODE_PATH}/.common/3d"
    }

Additionally, create a :file:`project.json` package definition file to set the
desired :term:`Maya` version and :term:`TD SVN` requirement.

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/project.json
    {
       "identifier": "project",
       "auto-use": true,
       "conditions": [
           "maya"
       ],
       "requirements": [
           "maya == 2016.*",
           "td-svn"
       ]
    }


Let's break down this :file:`project.json` package definition:

* The :ref:`auto-use <definition/auto-use>` keyword ensures that the package
  will always be added to the graph when this registry is included.

* The :ref:`conditions <definition/conditions>` keyword ensures that this
  definition is only being considered if 'maya' is part of the requests.

* The :ref:`requirements <definition/requirements>` keyword ensures that any
  requests for 'maya' will be constraint to a maya version of 2016.* and the
  "tdsvn" package is being added to the graph.


It is now possible to start :term:`Maya` anywhere under the project folder to
include all TD SVN scripts and modules.

.. code-block:: console

    >>> cd /jobs/ads/my_project
    >>> wiz run maya

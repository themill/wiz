Some environment variables should be set for a Job only so that DCC plugins or
applications would be affected only inside this environment.

.. _tutorial/project:

Project Configurations and Overrides
------------------------------------

Let's consider a fake project called ``my_project`` which can be replaced with
any existing projects::

    /jobs/ads/my_project/

Im order to use Wiz, :ref:`registries <registry/project>` need to exist in each
level of the hierarchy of a job. A tool called :term:`Chore` has been developed
to create that registry structure and fill it with definitions containing job
environment variables (similar to what :term:`mill_cd` returns).

Going forward, we will assume that the registry structure and the environment
variable definitions exists.

Let's set up :term:`Maya` for this job using Maya 2016 and adding the
:term:`TD SVN`.

Create a :file:`td-svn.json` package definition file to indicate the
location of the :term:`TD SVN` root folder within the project:

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/td-svn.json
    {
        "identifier": "td-svn",
        "description": "Environment for TD SVN.",
        "environ": {
            "TDSVN_ROOT": "${MILL_EPISODE_PATH}/.common/3d"
        },
        "requirements": [
            "job"
        ]
    }


Additionally, create a :file:`project.json` package definition file to set the
:term:`Maya` version and :term:`TD SVN` requirement.

.. code-block:: console

    >>> cat /jobs/ads/my_project/.wiz/registry/project.json
    {
       "identifier": "project",
       "auto-use": true,
       "constraints": [
           "maya == 2016.*"
       ],
       "requirements": [
           "td-svn"
       ]
    }


Let's break down this :file:`project.json` package definition:

* The :ref:`auto-use <definition/auto-use>` keyword ensure that the package will
  always be included in the graph when this registry is included.







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

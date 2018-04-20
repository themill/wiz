
Wiz is a command line tool and therefore has to be executed in a
:term:`Unix Shell`. To view help, run:

.. code-block:: console

    >>> wiz -h

View package definitions
------------------------

To start using Wiz it is beneficial to get an overview over the package
definitions that are currently available.

Running ``wiz list package`` will output a long list of packages found in the
detected registries. The registries are listed in order.

All these packages can be used with ``wiz use``.

.. code-block:: console

    >>> wiz list package
    Registries
    ----------------------------------------------
    [0] /mill3d/server/apps/WIZ/registry/primary
    [1] /mill3d/server/apps/WIZ/registry/secondary
    [2] /usr/people/claudiaz/.wiz/registry


    Package               Version    Registry   Description
    -------------------   --------   --------   --------------------
    maya                  2018       0          Maya Application.
    nuke                  11.1.1     0          Nuke Application.
    pod-maya [2018]       2.3.3      0          POD plugin for Maya.
    ...

.. seealso::
    :ref:`definition/package`

Running ``wiz list command`` will output a long list of commands found in the
detected registries.

All these commands can be used with ``wiz run``.

.. code-block:: console

    >>> wiz list command
    ...
    Command       Version    Registry   Description
    -----------   --------   --------   ----------------------
    houdini       16.5.323   0          Houdini Application.
    maya          2018       1          Maya Application.
    nuke          11.1.1     0          Nuke Application.
    ...

.. seealso::
    :ref:`definition/commands`

Package definitions are :term:`Json` files, which can be easily viewed and
edited in a text editor of your choice, but for convenience the ``wiz view``
command has been added.

This is what the :term:`Maya` package definition for example looks like:

.. code-block:: console

    >>> wiz view maya
    info: View definition: maya (2018)
    identifier: maya
    version: 2018
    description: Maya Application.
    registry: /mill3d/server/apps/WIZ/registry
    origin: /mill3d/server/apps/WIZ/registry/primary/maya/maya-2018.json
    system:
        arch: x86_64
        os: el >= 6, < 8
    command:
        maya: maya2018
        mayapy: mayapy
    environ:
        MAYA_MMSET_DEFAULT_XCURSOR: 1
        MAYA_LICENSE_METHOD: network
        MAYA_OFFSCREEN_HRB: 1
        MAYA_PLUGINS: ${MAYA_ROOT}/plugins/2018
        QT_COMPRESS_TABLET_EVENTS: 1
        LM_LICENSE_FILE: 27000@licence3.themill.com:27000@licence7.themill.com:27000@permit.la.themill.com:27000@licence6.themill.com:27000@master.mill.co.uk
        PATH: ${MAYA_LOCATION}/maya2018/bin:${PATH}
        AUTODESK_ADLM_THINCLIENT_ENV: /mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
    requirements:
            base-maya

Creating environments
---------------------

First, start with a very basic :term:`Maya` environment using ``wiz use``.

.. code-block:: console

    >>> wiz use maya
    info: Spawn shell: /bin/bash
    bash-4.2$

This spawned a clean bash shell, only extended by the environment variables set
in the `maya` package definition and its requirements. For convenience, some
additional environment variables are being set by Wiz itself, namely:

* LOGNAME
* USER
* PWD
* HOME
* DISPLAY

To check this, print the environment:

.. code-block:: console

    bash-4.2$ env
    MAYA_PLUGINS=/mill3d/server/apps/MAYA/plugins/2018
    QT_COMPRESS_TABLET_EVENTS=1
    MAYA_MMSET_DEFAULT_XCURSOR=1
    WIZ_VERSION=0.7.0
    USER=claudiaz
    PATH=/mill3d/server/apps/MAYA/linux-x86-64/maya2018/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    MAYA_ROOT=/mill3d/server/apps/MAYA
    PWD=/home/claudiaz/dev/wiz
    AUTODESK_ADLM_THINCLIENT_ENV=/mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
    LM_LICENSE_FILE=27000@licence3.themill.com:27000@licence7.themill.com:27000@permit.la.themill.com:27000@licence6.themill.com:27000@master.mill.co.uk
    MAYA_LOCATION=/mill3d/server/apps/MAYA/linux-x86-64
    SHLVL=1
    HOME=/usr/people/claudiaz
    LOGNAME=claudiaz
    MAYA_LICENSE_METHOD=network
    WIZ_PACKAGES=WyJiYXNlLW1heWEiLCAibWF5YT09MjAxOCJd
    DISPLAY=:0
    MAYA_OFFSCREEN_HRB=1
    _=/usr/bin/env


.. note::

    To only view a resolved environment, without creating a subshell, the
    ``wiz use --view`` command can be used.

    The returned output shows:

    * the registries in order
    * all packages with versions that have been resolved
    * all command aliases accessable in the environment
    * all environment variables set

    .. code-block:: console

        >>> wiz use --view maya

        Registries
        ----------------------------------------------
        [0] /mill3d/server/apps/WIZ/registry/primary
        [1] /mill3d/server/apps/WIZ/registry/secondary
        [2] /usr/people/claudiaz/.wiz/registry


        Package     Version   Registry   Description
        ---------   -------   --------   ------------------------------------------------
        base-maya   unknown   0          Base environment variables for Maya Application.
        maya        2018      0          Maya Application.


        Command   Value
        -------   --------
        maya      maya2018
        mayapy    mayapy


        Environment Variable           Environment Value
        ----------------------------   -------------------------------------------------------------
        AUTODESK_ADLM_THINCLIENT_ENV   /mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
        DISPLAY                        :0
        HOME                           /usr/people/claudiaz
        LM_LICENSE_FILE                27000@licence3.themill.com
                                       27000@licence7.themill.com
                                       27000@permit.la.themill.com
                                       27000@licence6.themill.com
                                       27000@master.mill.co.uk
        LOGNAME                        claudiaz
        MAYA_LICENSE_METHOD            network
        MAYA_LOCATION                  /mill3d/server/apps/MAYA/linux-x86-64
        MAYA_MMSET_DEFAULT_XCURSOR     1
        MAYA_OFFSCREEN_HRB             1
        MAYA_PLUGINS                   /mill3d/server/apps/MAYA/plugins/2018
        MAYA_ROOT                      /mill3d/server/apps/MAYA
        PATH                           /mill3d/server/apps/MAYA/linux-x86-64/maya2018/bin
                                       /usr/local/sbin
                                       /usr/local/bin
                                       /usr/sbin
                                       /usr/bin
                                       /sbin
                                       /bin
        QT_COMPRESS_TABLET_EVENTS      1
        USER                           claudiaz
        WIZ_PACKAGES                   WyJiYXNlLW1heWEiLCAibWF5YT09MjAxOCJd...
        WIZ_VERSION                    0.7.0

Now more plugins can be added to create a custom :term:`Maya` environment, i.e::

    >>> wiz use maya xmlf-maya pod-maya mtoa bonustools-maya
    bash-4.2$

To run the ``maya`` command, just run it in the subshell::

    >>> wiz use maya xmlf-maya pod-maya mtoa bonustools-maya
    bash-4.2$ maya

For convenience, commands can be automatically run once the environment got
resolved using ``--``, i.e::

    >>> wiz use "maya xmlf-maya pod-maya mtoa" -- maya

.. note::

    Each plugin dynamically adds itself to its respective menu / submenu,
    so that when dynamically loaded, the `Mill` menu is being dynamically
    populated.

    .. image:: ../image/maya_menu_some.png
        :width: 800px
        :align: center
        :alt: maya menu some

Default Application Environments
--------------------------------

Dynamic environments are very useful to test configurations and be able to take
out conflicting packages, but most of the artists will want pre-configured
environments. This can be achieved using requirements.

While the ``maya`` package definition was faily slim, defining only some basic
environment variables to get :term:`Maya` to run, the ``mill-maya`` package
definition includes all default :term:`Maya` plugins currently available.

This is the ``mill-maya`` package definition for 2018 (latest):

.. code-block:: console
    :emphasize-lines: 5, 16

    >>> wiz view mill-maya
    info: View definition: mill-maya (2018)
    identifier: mill-maya
    version:
        2018
    description: Maya Application with Mill Plugins.
    registry: /mill3d/server/apps/WIZ/registry/secondary
    origin: /mill3d/server/apps/WIZ/registry/secondary/maya/maya-2018.json
    system:
        arch: x86_64
        os: el >= 6, < 8
    command:
        maya: maya2018
        mayapy: mayapy
    requirements:
            maya ==2018
            mill-maya-start
            mtoa
            miasma-maya
            ...

To launch :term:`Maya` with this configuration, run::

    >>> wiz use mill-maya -- maya

Running Commands
----------------

A simpler way of launching application is to simply be able to run the command
aliases directly.

Since the ``maya`` command is specified in ``mill-maya`` (as you can see
with ``wiz view mill-maya``), instead of running::

    >>> wiz use mill-maya -- maya

as in the previous example, this can be executed to launch :term:`Maya` with
the ``mill-maya`` configuration::

    >>> wiz run maya

To specify a version
`PEP 440 <https://www.python.org/dev/peps/pep-0440/#version-specifiers>`_
for Python can be used::

    >>> wiz run maya==2016

Freeze Environment
------------------

Any wiz command dynamically creates and resolves a graph to determine the
final environment.

To lock down an environment and write it out as a normal wrapper, the
``wiz freeze`` command can be used.

.. code-block:: console

    >>> wiz freeze -o /tmp -f tcsh maya
    Indicate an identifier: test-maya
    Available aliases:
    - maya2018
    - mayapy
    Indicate a command (No command by default): maya2018

    >>> cat /tmp/test-maya
    #!/bin/tcsh -f
    #
    # Generated by wiz with the following environments:
    # - base-maya
    # - maya==2018
    #
    setenv MAYA_MMSET_DEFAULT_XCURSOR "1"
    setenv MAYA_ROOT "/mill3d/server/apps/MAYA"
    setenv MAYA_LOCATION "/mill3d/server/apps/MAYA/linux-x86-64"
    setenv MAYA_OFFSCREEN_HRB "1"
    setenv MAYA_LICENSE_METHOD "network"
    setenv MAYA_PLUGINS "/mill3d/server/apps/MAYA/plugins/2018"
    setenv QT_COMPRESS_TABLET_EVENTS "1"
    setenv WIZ_VERSION "0.7.0"
    setenv LOGNAME "claudiaz"
    setenv USER "claudiaz"
    setenv HOME "/usr/people/claudiaz"
    setenv PATH "/mill3d/server/apps/MAYA/linux-x86-64/maya2018/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
    setenv WIZ_PACKAGES "WyJiYXNlLW1heWEiLCAibWF5YT09MjAxOCJd"
    setenv DISPLAY ":0"
    setenv AUTODESK_ADLM_THINCLIENT_ENV "/mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml"
    setenv LM_LICENSE_FILE "27000@licence3.themill.com:27000@licence7.themill.com:27000@permit.la.themill.com:27000@licence6.themill.com:27000@master.mill.co.uk"
    maya2018 $argv:q

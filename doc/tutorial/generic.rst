
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
    [0] /mill3d/server/apps/WIZ/registry/primary/default
    [1] /mill3d/server/apps/WIZ/registry/secondary/default
    [2] /usr/people/{username}/.wiz/registry


    Package               Version    Registry   Description
    -------------------   --------   --------   --------------------
    maya::maya            2018       0          Maya Application.
    nuke::nuke            11.1.1     0          Nuke Application.
    maya::pod [2018]      2.3.3      0          POD plugin for Maya.
    ...

.. seealso:: :ref:`definition`

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

.. seealso:: :ref:`definition/command`

Package definitions are :term:`Json` files, which can be easily viewed and
edited in a text editor of your choice, but for convenience the ``wiz view``
command has been added.

This is what the :term:`Maya` package definition for example looks like:

.. code-block:: console

    >>> wiz view maya
    info: Command found in definition: mill-maya==2018
    info: View definition: maya::maya==2018.4.7
    identifier: maya
    version: 2018.4.7
    namespace: maya
    description: Autodesk Maya Application.
    registry: /mill3d/server/apps/WIZ/registry/primary/default
    definition-location: /mill3d/server/apps/WIZ/registry/primary/default/maya/maya-2018.4.7.json
    install-location: /mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07
    system:
        arch: x86_64
        os: el >= 6, < 8
    command:
        maya: maya2018
        mayapy: mayapy
    environ:
        MAYA_MMSET_DEFAULT_XCURSOR: 1
        MAYA_LOCATION: ${INSTALL_LOCATION}
        PYTHONPATH: ${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}
        MAYA_APP_DIR: /mill3d/work/${LOGNAME}/maya2018-UPD4P07:${MAYA_APP_DIR}
        MAYA_PLUGINS: /mill3d/server/apps/MAYA/plugins/2018
        QT_COMPRESS_TABLET_EVENTS: 1
        MAYA_VERSION: 2018
        PATH: ${INSTALL_LOCATION}/bin:${PATH}
        MAYA_OFFSCREEN_HRB: 1
        LD_LIBRARY_PATH: ${INSTALL_LOCATION}/lib:${LD_LIBRARY_PATH}
        AUTODESK_ADLM_THINCLIENT_ENV: /mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
    requirements:
        maya::licence

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
* HOME
* DISPLAY
* PATH (with only executable folders from the workstation)
* XAUTHORITY

To check this, print the environment:

.. code-block:: console

    bash-4.2$ env
    MAYA_PLUGINS=/mill3d/server/apps/MAYA/plugins/2018
    HOSTNAME=la3d15.mill-la.com
    MAYA_VERSION=2018
    QT_COMPRESS_TABLET_EVENTS=1
    MAYA_MMSET_DEFAULT_XCURSOR=1
    WIZ_VERSION=2.5.0
    MAYA_APP_DIR=/mill3d/work/claudiaz/maya2018-UPD4P07
    USER=claudiaz
    LD_LIBRARY_PATH=/mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07/lib
    WIZ_CONTEXT=eJyFizsOwjAQBa8SuY68/CRocgBOgBTLxWIvaJGdWF4blJweUvFpqJ40b8YYFdjR4Ei1jYo4YddtVuuD3un9QoQLKds2RkHkELYehPKdMmBKAqdjD5muLCVPkDJHfK2nC9ZQlvpvI+TGwf9Wt/EsoB88v8XPu0qGRGMKBC5g9Yzzt62sfQJq+Uqf
    PATH=/mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    PWD=/mill3d/server/apps/PYTHON/packages
    AUTODESK_ADLM_THINCLIENT_ENV=/mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
    MILL_JOB_LOCATION=LA
    LM_LICENSE_FILE=27000@licence6.themill.com
    MAYA_LOCATION=/mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07
    MILL_SITE=la
    SHLVL=1
    HOME=/usr/people/claudiaz
    LOGNAME=claudiaz
    PYTHONPATH=/mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07/lib/python2.7/site-packages
    MAYA_LICENSE_METHOD=network
    DISPLAY=:0
    MAYA_OFFSCREEN_HRB=1
    XAUTHORITY=/run/gdm/auth-for-claudiaz-RPzH9x/database
    _=/usr/bin/env

.. note::

    To only view a resolved environment, without creating a sub-shell, the
    ``wiz use --view`` command can be used.

    The returned output shows:

    * the registries in order
    * all packages with versions that have been resolved
    * all command aliases accessible in the environment
    * all environment variables set

    .. code-block:: console

        >>> wiz use --view maya

        Registries
        ----------------------------------------------
        [0] /mill3d/server/apps/WIZ/registry/primary/default
        [1] /mill3d/server/apps/WIZ/registry/secondary/default
        [2] /jobs/.wiz/registry/default
        [3] /usr/people/{username}/.wiz/registry

        Package         Version    Registry   Description
        -------------   --------   --------   ---------------------------------------
        maya::licence   unknown    0          Licence for Autodesk Maya Applications.
        maya::maya      2018.4.7   0          Autodesk Maya Application.
        site            unknown    2          Current Mill site.

        Command   Value
        -------   --------
        maya      maya2018
        mayapy    mayapy

        Environment Variable           Environment Value
        ----------------------------   ----------------------------------------------------------------------------------
        AUTODESK_ADLM_THINCLIENT_ENV   /mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
        DISPLAY                        :0
        HOME                           /usr/people/claudiaz
        HOSTNAME                       la3d15.mill-la.com
        LD_LIBRARY_PATH                /mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07/lib
        LM_LICENSE_FILE                27000@licence6.themill.com
        LOGNAME                        claudiaz
        MAYA_APP_DIR                   /mill3d/work/claudiaz/maya2018-UPD4P07
        MAYA_LICENSE_METHOD            network
        MAYA_LOCATION                  /mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07
        MAYA_MMSET_DEFAULT_XCURSOR     1
        MAYA_OFFSCREEN_HRB             1
        MAYA_PLUGINS                   /mill3d/server/apps/MAYA/plugins/2018
        MAYA_VERSION                   2018
        MILL_JOB_LOCATION              LA
        MILL_SITE                      la
        PATH                           /mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07/bin
                                       /usr/local/sbin
                                       /usr/local/bin
                                       /usr/sbin
                                       /usr/bin
                                       /sbin
                                       /bin
        PYTHONPATH                     /mill3d/server/apps/MAYA/linux-x86-64/maya2018-UPD4P07/lib/python2.7/site-packages
        QT_COMPRESS_TABLET_EVENTS      1
        USER                           claudiaz
        WIZ_CONTEXT                    eJyFizsOwjAQBa8SuY68/CRocgBOgBTLxWIvaJGdWF4blJweUv...
        WIZ_VERSION                    2.5.0
        XAUTHORITY                     /run/gdm/auth-for-claudiaz-RPzH9x/database

Now more plugins can be added to create a custom :term:`Maya` environment, i.e::

    >>> wiz use maya maya::xmlf maya::pod mtoa maya::bonustools
    bash-4.2$

To run the ``maya`` command, just run it in the subshell::

    >>> wiz use maya maya::xmlf maya::pod mtoa maya::bonustools
    bash-4.2$ maya

For convenience, commands can be automatically run once the environment got
resolved using ``--``, i.e::

    >>> wiz use maya maya::xmlf maya::pod mtoa -- maya

.. note::

    Each plugin dynamically adds itself to its respective menu / submenu,
    so that when dynamically loaded, the `Mill` menu is being dynamically
    populated.

    .. image:: ../image/maya_menu_some.png
        :width: 800px
        :align: center
        :alt: maya menu some

.. warning::

    When executing a command using an environment variable from the resolved
    context, the dollar sign must be escaped in order to prevent substituting
    the variable with the external environment:

    .. code-block:: console

        >>> wiz use python -- echo $PIP_CONFIG_FILE
        PIP_CONFIG_FILE: Undefined variable.

        >>> wiz use python -- echo \$PIP_CONFIG_FILE
        info: Start command: echo '$PIP_CONFIG_FILE'
        /mill3d/server/apps/PYTHON/el7-x86-64/python-3.6.6/etc/pip/pip.conf

Default Application Environments
--------------------------------

Dynamic environments are very useful to test configurations and be able to take
out conflicting packages, but most of the artists will want pre-configured
environments. This can be achieved using requirements.

While the ``maya`` package definition was fairly slim, defining only some basic
environment variables to get :term:`Maya` to run, the ``mill-maya`` package
definition includes all default :term:`Maya` plugins currently available.

This is the ``mill-maya`` package definition for 2018 (latest):

.. code-block:: console
    :emphasize-lines: 4, 15

    >>> wiz view mill-maya
    info: View definition: mill-maya==2018
    identifier: mill-maya
    version: 2018
    description: Maya Application with Mill Plugins.
    registry: /mill3d/server/apps/WIZ/registry/secondary/default
    definition-location: /mill3d/server/apps/WIZ/registry/secondary/default/maya/mill-maya-2018.json
    command:
        maya: maya2018
        mayapy: mayapy
    requirements:
        maya::maya >=2018, <2019
        maya::mill-start
        maya::mtoa
        ...

To launch :term:`Maya` with this configuration, run::

    >>> wiz use mill-maya -- maya

Running Commands
----------------

A simpler way of launching application is to simply be able to run the command
aliases directly.

Since the ``maya`` command is specified in ``mill-maya`` (as you can see
with ``wiz view mill-maya``), :term:`Maya` could also be launched with the
``mill-maya`` configuration as follows::

    >>> wiz run maya

A version specifier as those described in the :term:`PEP 440` specification can
be used::

    >>> wiz run maya==2016

Freeze Environment
------------------

Any wiz command dynamically creates and resolves a graph to determine the
final environment.

To lock down an environment as a new Wiz definition, the ``wiz freeze`` command
can be used:

.. code-block:: console

    >>> wiz freeze maya mtoa -o ~/.wiz/registry
    Indicate an identifier: my-maya
    Indicate a description: This is my Maya
    Indicate a version [0.1.0]:

    >>> wiz view my-maya
    info: View definition: my-maya (0.1.0)
    identifier: my-maya
    version: 0.1.0
    description: This is my Maya
    registry: /Users/claudiaz/.wiz/registry
    origin: /Users/claudiaz/.wiz/registry/MyMaya-0.1.0.json
    command:
        maya: maya2018
        mayapy: mayapy
    environ:
        MAYA_MMSET_DEFAULT_XCURSOR: 1
        MAYA_ROOT: /mill3d/server/apps/MAYA
        ARNOLD_SHADERS_MTOA: /mill3d/server/apps/ARNOLD/mtoa/maya-2018/MtoA-2.1.0.1-20_arnold-5.0.2.4_g8a6d063/shaders
        MAYA_MODULE_PATH: /mill3d/server/apps/ARNOLD/mtoa/maya-2018/MtoA-2.1.0.1-20_arnold-5.0.2.4_g8a6d063
        MAYA_OFFSCREEN_HRB: 1
        MAYA_LOCATION: /mill3d/server/apps/MAYA/linux-x86-64
        MAYA_PLUGINS: /mill3d/server/apps/MAYA/plugins/2018
        QT_COMPRESS_TABLET_EVENTS: 1
        MAYA_LICENSE_METHOD: network
        WIZ_VERSION: 0.7.1
        LOGNAME: claudiaz
        USER: claudiaz
        HOME: /usr/people/claudiaz
        PATH: /mill3d/server/apps/MAYA/linux-x86-64/maya2018/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
        WIZ_PACKAGES: WyJtdG9hWzIwMThdPT0yLjEuMC4xIiwgImJhc2UtbWF5YSIsICJtYXlhPT0yMDE4Il0=
        DISPLAY: None
        AUTODESK_ADLM_THINCLIENT_ENV: /mill3d/server/system/LICENCE/AUTODESK/ADLM/maya2018/adlm.xml
        LM_LICENSE_FILE: 27000@licence3.themill.com:27000@licence7.themill.com:27000@permit.la.themill.com:27000@licence6.themill.com:27000@master.mill.co.uk

After viewing and maybe testing the definition, it should be removed from the
personal registry, as keeping it will overwrite the "maya2018" and "mayapy"
commands from the secondary registry, which is undesirable.

.. code-block:: console

    >>> rm ~/.wiz/registry/my-maya-0.1.0.json

It is also possible to lock down an environment and write it out as a
:term:`C-Shell` or :term:`Bash` wrapper:

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

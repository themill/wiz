.. _tutorial:

********
Tutorial
********

A quick dive into using Wiz.

Please ensure the :ref:`registry/setup` has been performed before continuing
with this tutorial.

.. toctree::
    :maxdepth: 1

    tools

Using wiz
=========

.. code-block:: console

    >>> wiz -h

wiz list command

wiz list package

View package definition
-----------------------

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

Create environment
------------------

.. code-block:: console

    >>> wiz use --view maya

    Registries
    ------------------------------------
    [0] /mill3d/server/apps/WIZ/registry


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
    WIZ_VERSION                    0.2.0


.. code-block:: console

    >>> wiz use --view maya xmlf-maya

    Registries
    ------------------------------------
    [0] /mill3d/server/apps/WIZ/registry


    Package     Version   Registry   Description
    ---------   -------   --------   ------------------------------------------------
    xmlf-maya   17        0          XMLF plugin for Maya.
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
    MAYA_MODULE_PATH               /mill3d/server/apps/MAYA/plugins/2018/mill/xmlf/xmlf.v17
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
    WIZ_PACKAGES                   WyJ4bWxmLW1heWE9PTE3IiwgImJhc2UtbWF5YSIsICJtYXlhPT...
    WIZ_VERSION                    0.2.0


Run Command
-----------

.. code-block:: console

    >>> wiz run maya

.. code-block:: console

    >>> wiz run maya==2016

Freeze Environment
------------------

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


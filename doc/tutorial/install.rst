.. _tutorial/install/qip:

Installing from Qip
===================

:term:`Qip` is a tool to install python packages into a bundled directory
structure. It can also create Wiz package definitions for any packages that
don't include one already.

Once package data has been installed to their location on the file system,
``wiz install`` can be run to install those definitions to a registry.

Let's install a python package with all its requirements as follows::

    >>> qip install mlog

Now install the corresponding definitions into your personal registry::

    >>> wiz install /tmp/qip/definitions/* --registry ~

.. warning::

    If the data is moved between the :term:`qip` install and wiz install,
    :option:`wiz edit --set` should be used to set the ``install-location`` or
    ``install-root`` to the appropriate new data location. This step needs to be
    taken BEFORE the wiz install.

    .. code-block:: console

        >>> wiz edit --set install-root tmp/qip/packages /tmp/qip/definitions/*

You can now use all the typical wiz commands to view and use that package::

    >>> wiz use mlog --view
    >>> wiz use mlog -- python
    import mlog

.. hint::

    Installing a package with :term:`Qip` while setting the
    :option:`--definition-path <qip install --definition-path>` to your personal
    registry will automatically make them available for development.

    For example. With the following command a definition is created in the
    personal registry with the ``install-location`` set to data linking back
    to the source code for development::

        >>> qip install . -e --definition-path ~/.wiz/registry

    There is no further install necessary for development.

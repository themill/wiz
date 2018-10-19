.. _tutorial/install:

Installing from Qip
===================

:term:`Qip` is a tool to install python packages into a bundled directory
structure. It can also create Wiz package definitions for any packages that
don't include one already.

Once package data has been installed to their location on the file system,
``wiz install`` can be run to install those definitions to a registry.

Let's install a python package with all its requirements as follow::

    >>> qip install mlog --output-path /tmp/python-data --definition-path /tmp/python-definition

Now install the corresponding definitions in your personal registry::

    >>> cd /tmp/my-install-test
    >>> wiz install /tmp/python-definition/* --registry-path ~

You can now use all the typical wiz commands to view and use that package::

    >>> wiz use mlog --view
    >>> wiz use mlog -- python
    import mlog

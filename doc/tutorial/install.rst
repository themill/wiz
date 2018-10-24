.. _tutorial/install/qip:

Installing from Qip
===================

:term:`Qip` is a tool to install python packages into a bundled directory
structure. It can also create Wiz package definitions for any packages that
don't include one already.

Once package data has been installed to their location on the file system,
``wiz install`` can be run to install those definitions to a registry.

Let's install a python package with all its requirements as follow::

    >>> qip install mlog --output-path /tmp/data --definition-path /tmp/definition

Now install the corresponding definitions in your personal registry::

    >>> cd /tmp/my-install-test
    >>> wiz install /tmp/definition/* --registry-path ~

You can now use all the typical wiz commands to view and use that package::

    >>> wiz use mlog --view
    >>> wiz use mlog -- python
    import mlog

.. hint::

    Installing a package with :term:`Qip` while setting the definition output to
    your personal registry will automatically make them available for
    development.

    For example. With the following command a definition is created in the
    personal registry with the ``install-location`` set to data linking back
    to the source code for development:

        >>> qip install . -e --output-path /tmp/dev --registry-path ~

    There is no further install necessary for development.

.. _tutorial/install:

Installing from Qip
===================

:term:`Qip` is a tool to install packages into a bundled directory structure.
It will also create Wiz package definitions for any packages that don't include
one already.

Once package data has been installed to their location on the file system, using
:term:`Qip`, ``wiz install`` can be run to install those definitions to a
registry.

To try this, lets ``qip install`` a package to /tmp::

    >>> qip install mlog --output /tmp/my-install-test

Navigate to the :term:`Qip` package install location on the file system and
install the definition to your personal registry:

.. code-block:: console

    >>> cd /tmp/my-install-test
    >>> wiz --definition-search-paths . --definition-search-depth 2 install mlog/mlog-0.2.1/mlog-0.2.1.json --registry-path ~ --with-requirements
    info: Successfully installed mlog-0.2.1 to ~/.wiz/registry registry.
    info: Successfully installed sawmill-0.2.1 to ~/.wiz/registry registry.
    info: Successfully installed html2text-2016.4.2 to ~/.wiz/registry registry.
    info: Successfully installed pystache-0.5.4 to ~/.wiz/registry registry.
    info: Successfully installed colorama-0.3.9 to ~/.wiz/registry registry.
    >>> l ~/.wiz/registry/
    colorama-0.3.9.json
    html2text-2016.4.2.json
    mlog-0.2.1.json
    pystache-0.5.4.json
    sawmill-0.2.1.json

With the package and all of its dependencies installed in your personal registry,
you can now use all the typical wiz commands to view and use that package.

    >>> wiz use mlog --view
    >>> wiz use mlog -- python
    import mlog

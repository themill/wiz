.. _introduction:

************
Introduction
************

Wiz is a environment manager which can resolve a context or execute a command
from one or several package requests. The resolved context contains the
environment mapping and a list of accessible command aliases.

The packages are defined in :ref:`package definitions <definition>` which are
stored in one or several :ref:`registries <registry>`.

Example::

    wiz use python
    wiz use nuke ldpk-nuke
    wiz use nuke -- /path/to/script.nk

A command can also be executed from a resolved context via a command alias which
is extracted from its corresponding package.

Example::

    wiz run nuke
    wiz run nuke -- /path/to/script.nk
    wiz run python


All available packages and command can be listed as follow::

    wiz list package
    wiz list command

It is also possible to search a specific package or command as follow::

    wiz search python

Use ``wiz --help`` to see all the options.

.. _introduction:

************
Introduction
************

Wiz is an environment management framework which consists of a :term:`Python`
API and a command line tool. It can be used to run a command within a specific
environment mapping resolved from one or several package requests (e.g.
["nuke==12.2.*", "ldpk-nuke"]).

The packages are defined in :ref:`package definitions <definition>` which are
stored in one or several :ref:`registries <registry>`.

The command line tool can be used as follows::

    wiz use python
    wiz use nuke ldpk-nuke
    wiz use nuke -- /path/to/script.nk

Equivalent commands can be executed using the Python API::

    >>> context = wiz.resolve_context(["nuke", "ldpk-nuke"])
    >>> subprocess.call(context["command"]["nuke"], environ=context["environ"])

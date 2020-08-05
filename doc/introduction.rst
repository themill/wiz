.. _introduction:

************
Introduction
************

Wiz is an environment management framework which consists of a :term:`Python`
API and a command line tool. It can be used to run a command within a
deterministic environment resolved from one or several package requests.

The packages are defined in :ref:`package definitions <definition>` which are
stored in one or several :ref:`registries <registry>`.

The command line tool can be used as follows::

    wiz use "app==2.*" my-plugin -- AppExe /path/to/script

Equivalent commands can be executed using the Python API::

    import subprocess
    import wiz

    # Resolve context.
    context = wiz.resolve_context(["app==2.*", "my-plugin"])

    # Run command within environment.
    command = context["command"]["AppExe"]
    subprocess.call(command, environ=context["environ"])


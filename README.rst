###
Wiz
###

Wiz is an environment management framework which consists of a Python API and a
command line tool. It can be used to run a command within a deterministic
environment resolved from one or several package requests (e.g.
["python==2.7.*", "app==12.*"]).

The packages are defined in package definitions which are stored in one or
several registries.

The command line tool can be used as follows::

    wiz use app my-plugin -- AppExe /path/to/script

Equivalent commands can be executed using the Python API::

    >>> context = wiz.resolve_context(["app", "my-plugin"])
    >>> command = context["command"]["AppExe"]
    >>> subprocess.call(command, environ=context["environ"])

*************
Documentation
*************

Full documentation, including installation and setup guides, can be found at
http://rtd.themill.com/docs/wiz/en/stable/

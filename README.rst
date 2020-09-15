###
Wiz
###

.. image:: https://img.shields.io/pypi/v/wiz-env.svg
    :target: https://pypi.python.org/pypi/wiz-env
    :alt: PyPi Package Link

.. image:: https://travis-ci.org/themill/wiz.svg?branch=master
    :target: https://travis-ci.org/themill/wiz
    :alt: Continuous Integration

.. image:: https://readthedocs.org/projects/wiz/badge/?version=stable
    :target: https://wiz.readthedocs.io/en/stable/
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/group-join%20discussion-blue
    :target: https://groups.google.com/g/wiz-framework
    :alt: Google Group Page

.. image:: https://img.shields.io/badge/license-LGPL%20v3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0
    :alt: License Link

Wiz is an environment management framework which consists of a Python API and a
command line tool. It can be used to run a command within a deterministic
environment resolved from one or several package requests.

The packages are defined in package definitions which are stored in one or
several registries.

The command line tool can be used as follows::

    >>> wiz use "app==2.*" my-plugin -- AppExe /path/to/script

Equivalent commands can be executed using the Python API:

.. code-block:: python

    import subprocess
    import wiz

    # Resolve context.
    context = wiz.resolve_context(["app==2.*", "my-plugin"])

    # Run command within environment.
    command = context["command"]["AppExe"]
    subprocess.call(command, environ=context["environ"])

*************
Documentation
*************

Full documentation, including installation and setup guides, can be found at
https://wiz.readthedocs.io/en/stable/

*********
Copyright
*********

Copyright (C) 2018, The Mill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

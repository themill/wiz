.. _getting_started:

***************
Getting started
***************

.. highlight:: shell

Once :ref:`installed <installing>`, the command line tool can be used in a shell
as follows::

    >>> wiz -h

At this point, there are no packages available yet as no registries are defined.
Let's get started by creating a :ref:`package definition <definition>` to run
the :term:`Python` interpreter.

First, create our first registry directory to store this definition::

    >>> mkdir /tmp/registry

A definition is a json file, so create :file:`/tmp/registry/python.json` with this 
content::

    {
        "identifier": "python"
    }

You can now discover the package using the command line tool::

    >>> wiz -r /tmp/registry list package

    Registries
    -----------------
    [0] /tmp/registry


    Package   Version   Registry   Description
    -------   -------   --------   -----------
    python    -         0          -

.. note::

    We are using the :option:`wiz -r` option throughout this page to indicate
    which registry to parse. Later we will see how to set up default registries
    with a :ref:`configuration file <configuration/registry_paths>`.

Python is defined with a version, so we can add it to the definition along with
a short description::

    {
        "identifier": "python",
        "version": "2.7.16",
        "description": "Python interpreter environment."
    }

This change is reflected when listing the package::

    >>> wiz -r /tmp/registry list package

    Registries
    -----------------
    [0] /tmp/registry


    Package   Version   Registry   Description
    -------   -------   --------   -------------------------------
    python    2.7.16    0          Python interpreter environment.

We now have a first package, but it is not very useful as it does not define any
commands or environment variables. Let's modify the definition to associate it
with the corresponding Python interpreter installed on your system::

    {
        "identifier": "python",
        "version": "2.7.16",
        "description": "Python interpreter environment.",
        "install-location": "/path/to/python-2.7.12",
        "command": {
            "python": "python2.7"
        },
        "environ": {
            "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
            "LD_LIBRARY_PATH": "${INSTALL_LOCATION}/lib:${INSTALL_LOCATION}/lib/python2.7/lib-dynload:${LD_LIBRARY_PATH}",
            "PYTHONPATH": "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}",
            "PIP_CONFIG_FILE": "${INSTALL_LOCATION}/etc/pip/pip.conf"
        }
    }

The Python interpreter is compiled for a specific architecture, so add the
:ref:`definition/system` keyword to lock it to your system::

    {
        "identifier": "python",
        "version": "2.7.16",
        "description": "Python interpreter environment.",
        "install-location": "/path/to/python-2.7.12",
        "system": {
            "arch": "x86_64",
            "os": "el >= 7, < 8"
        },
        "command": {
            "python": "python2.7"
        },
        "environ": {
            "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
            "LD_LIBRARY_PATH": "${INSTALL_LOCATION}/lib:${INSTALL_LOCATION}/lib/python2.7/lib-dynload:${LD_LIBRARY_PATH}",
            "PYTHONPATH": "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
        }
    }

.. warning::

    This example is running on Linux EL 7. Adjust the :ref:`definition/system`
    value to your own architecture, otherwise the definition will be filtered
    out.

You can now run python within this environment::

    >>> wiz -r /tmp/registry use python -- python
    info: Start command: python2.7
    Python 2.7.16 (default, Jun 19 2019, 07:41:28)

Now let's add another definition in :file:`/tmp/registry/python3.json` to create
an environment for Python 3::

    {
        "identifier": "python",
        "version": "3.7.8",
        "description": "Python interpreter environment.",
        "install-location": "/path/to/python-3.7.8",
        "system": {
            "arch": "x86_64",
            "os": "el >= 7, < 8"
        },
        "command": {
            "python": "python3.7"
        },
        "environ": {
            "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
            "LD_LIBRARY_PATH": "${INSTALL_LOCATION}/lib:${INSTALL_LOCATION}/lib/python3.7/lib-dynload:${LD_LIBRARY_PATH}",
            "PYTHONPATH": "${INSTALL_LOCATION}/lib/python3.7/site-packages:${PYTHONPATH}"
        }
    }

.. note::

    Note that the name of the :term:`JSON` file does not matter as only the
    identifier is being used to identify the package.

Running the same command as before will now launch the Python 3.7 interpreter as
it has a higher version number::

    >>> wiz -r /tmp/registry use python -- python
    info: Start command: python3.7
    Python 3.7.8 (v3.7.8, Feb 24 2020, 17:52:18)

You can still explicitly require the Python 2.7 interpreter by adjusting the
package request::

    >>> wiz -r /tmp/registry use "python==2.*" -- python
    info: Start command: python2.7
    Python 2.7.16 (default, Jun 19 2019, 07:41:28)

We could now create another definition for a Python library that we would like
to use with Python 2.7 and Python 3.7. Let's use `numpy 1.16.6
<https://pypi.org/project/numpy/1.16.6/>`_ which is compatible with both Python
versions::

    >>> pip2.7 install numpy==1.16.6
    >>> pip3.7 install numpy==1.16.6

So far we always had one package extracted per definition, but as the two Python
libraries have the same version, we will use the :ref:`definition/variants`
keyword to define both libraries within a single
:file:`/tmp/registry/numpy.json` definition::

    {
        "identifier": "numpy",
        "version": "1.16.6",
        "description": "NumPy is the fundamental package for array computing with Python.",
        "system": {
            "arch": "x86_64",
            "os": "el >= 7, < 8"
        },
        "environ": {
            "PYTHONPATH": "${INSTALL_LOCATION}:${PYTHONPATH}"
        },
        "variants": [
            {
                "identifier": "3.7",
                "install-location": "/path/to/numpy/lib/python3.7/site-packages",
                "requirements": [
                    "python >=3.7, <3.8"
                ]
            },
            {
                "identifier": "2.7",
                "install-location": "/path/to/numpy/lib/python2.7/site-packages",
                "requirements": [
                    "python >=2.7, <2.8"
                ]
            }
        ]
    }

Let's list all available packages to ensure that the two Numpy packages are
properly extracted::

    >>> wiz -r /tmp/registry list package -a

    Registries
    -----------------
    [0] /tmp/registry


    Package       Version   Registry   Description
    -----------   -------   --------   -----------------------------------------------------------------
    numpy [3.7]   1.16.6    0          NumPy is the fundamental package for array computing with Python.
    numpy [2.7]   1.16.6    0          NumPy is the fundamental package for array computing with Python.
    python        3.7.8     0          Python interpreter environment.
    python        2.7.16    0          Python interpreter environment.

The :ref:`definition/requirements` keyword is set for each variant to ensure
that the correct Python environment will be resolved.

Run the following command::

    >>> wiz -r /tmp/registry use numpy -- python
    info: Start command: python3.7
    Python 3.7.8 (v3.7.8, Feb 24 2020, 17:52:18)
    >>> import numpy
    >>> numpy.__file__
    '/path/to/numpy/lib/python3.7/site-packages'

By simply requesting the package by its identifier, it will pick up the first
compatible variant by default and resolve the library for Python 3.7. You can
explicitly request another variant::

    >>> wiz -r /tmp/registry use "numpy[2.7]" -- python
    info: Start command: python2.7
    Python 2.7.16 (default, Jun 19 2019, 07:41:28)
    >>> import numpy
    >>> numpy.__file__
    '/path/to/numpy/lib/python2.7/site-packages'

You can also explicitly request Python 2.7 and the default version of Numpy.
The first variant will then be incompatible and the expected environment will be
returned::

    >>> wiz -r /tmp/registry use numpy "python==2.7.*" -- python
    info: Start command: python2.7
    Python 2.7.16 (default, Jun 19 2019, 07:41:28)
    >>> import numpy
    >>> numpy.__file__
    '/path/to/numpy/lib/python2.7/site-packages'

Incompatible package requests will return an error::

    >>> wiz -r /tmp/registry use "numpy[2.7]" "python==3.*" -- python
    error: Failed to resolve graph at combination #1:

    The dependency graph could not be resolved due to the following requirement conflicts:
      * python >=2.7, <2.8 	[numpy[2.7]==1.16.6]
      * python ==3.* 	[root]

The same logic can be applied for creating quick environments combining
applications, plugins, libraries, etc.. Definitions could also be created to
store a set of environment variables useful for a specific context.

.. seealso:: :ref:`definition`

Many more registries can be used to contextualize the definitions in a
determinist priority order.

.. seealso:: :ref:`registry`

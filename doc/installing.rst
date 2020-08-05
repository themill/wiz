.. _installing:

**********
Installing
**********

.. highlight:: bash

.. note::

    Using :term:`Virtualenv` is recommended when evaluating or running locally.

Installation is simple with :term:`Pip`::

    pip install wiz-env

.. _installing/source:

Installing from source
======================

You can also install manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://github.com/themill/wiz/archive/master.zip>`_ or
cloning the public repository::

    git clone git@github.com:themill/wiz.git

Then you can build and install the package into your current Python
environment::

    pip install .

If actively developing, you can perform an editable install that will link to
the project source and reflect any local changes made instantly::

    pip install -e .

.. note::

    If you plan on building documentation and running tests, run the following
    command instead to install required extra packages for development::

        pip install -e .[dev]

Alternatively, just build locally and manage yourself::

    python setup.py build

.. _installing/source/options:

Building with custom options
----------------------------

You can also embed custom :ref:`configuration file <configuration>` and
:ref:`plugins <plugins>` with the package. This can be particularly useful
when deploying Wiz with a common configuration for a group of users::

    python setup.py build_py \
    --wiz-config-file=/path/to/config.toml \
    --wiz-plugin-path=/path/to/custom/plugins/

The package built can then be bundled into a distribution that can be easily
released into a `custom index
<https://packaging.python.org/guides/hosting-your-own-index/>`_::

    python setup.py bdist
    python setup.py bdist_wheel

.. warning::

    If your plugin contains additional requirements, the :file:`setup.py` file
    will have to be patched accordingly, to ensure that the plugin works as
    expected.

.. _installing/source/doc:

Building documentation from source
----------------------------------

Ensure you have installed the 'extra' packages required for building the
documentation::

    pip install -e .[doc]

Then you can build the documentation with the command::

    python setup.py build_sphinx

View the result in your browser at::

    file:///path/to/wiz/build/doc/html/index.html

.. _installing/source/test:

Running tests against the source
--------------------------------

Ensure you have installed the 'extra' packages required for running the tests::

    pip install -e .[test]

Then run the tests as follows::

    python setup.py -q test

You can also generate a coverage report when running tests::

    python setup.py -q test --addopts "--cov --cov-report=html"

View the generated report at::

    file:///path/to/wiz/htmlcov/index.html


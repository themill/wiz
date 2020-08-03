"""
Converting test folders into modules allows to use similar file names within
structure::

    test/
        __init__.py
        integration/
            __init__.py
            test_something.py
        unit/
            __init__.py
            test_something.py

.. seealso::

    https://docs.pytest.org/en/latest/goodpractices.html#tests-outside-application-code

"""

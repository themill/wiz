.. _plugins:

*************
Using Plugins
*************

We can use :ref:`configuration files <configuration>` to customize Wiz, but we
can also extend the configuration mapping with dynamic values using
:term:`Python` plugins.

Plugins are being discovered and loaded just after configuration mapping has
been created from :ref:`configuration files <configuration>`.

.. _plugins/default:

Default plugins
---------------

The following plugins are used by default.

.. _plugins/default/environ:

environ
~~~~~~~

This plugin adds initial environment variable to the configuration mapping.

.. literalinclude:: ../source/wiz/package_data/plugins/environ.py
   :language: python

.. _plugins/default/installer:

installer
~~~~~~~~~

This plugin adds an installer callback to the configuration mapping to
indicate how a definition can be installed using ``wiz install``.

.. literalinclude:: ../source/wiz/package_data/plugins/installer.py
   :language: python

.. _plugins/new:

Adding new plugins
------------------

More plugins paths can be added using :envvar:`WIZ_PLUGIN_PATHS`. It is also
possible to define personal plugins in :file:`~/.wiz/plugins`.

The default plugins will always be loaded first, followed by the plugins defined
by :envvar:`WIZ_PLUGIN_PATHS` in reversed order. The personal plugins are always
loaded last.

A plugin is uniquely identified by the :attr:`IDENTIFIER` data string.
Therefore, you can overwrite a plugin by re-using the same identifier.

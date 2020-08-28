.. _plugins:

*************
Using Plugins
*************

We can use :ref:`configuration files <configuration>` to customize Wiz, but we
can also extend the configuration mapping with dynamic values using
:term:`Python` plugins.

.. hint::

    Plugins are being discovered and loaded just after configuration mapping has
    been created from :ref:`configuration files <configuration>`. So any
    modification to the configuration mapping done in the plugins will always
    overwrite the content of the :ref:`configuration files <configuration>`.

.. _plugins/default:

Default plugins
---------------

The following plugins are located in :file:`wiz/package_data/plugins`. They are
used by default, unless modified during the :ref:`installation process
<installing/source/options>`.

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

.. _plugins/shell:

shell
~~~~~

There are several default shell plugins that can be used or modified.
The plugins are only registered on the appropriate operating system and if
the application path exists.

.. _plugins/shell/bash:

bash
^^^^

Bash is the default shell on Linux.

.. literalinclude:: ../source/wiz/package_data/plugins/bash.py
   :language: python

.. _plugins/shell/gitbash:

gitbash
^^^^^^^

`Git-Bash <https://gitforwindows.org/>`_ is a very popular bash shell for
Windows.

.. literalinclude:: ../source/wiz/package_data/plugins/gitbash.py
   :language: python

cmd
^^^

`CMD <https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands>`_
is the native DOS shell on Windows.

.. literalinclude:: ../source/wiz/package_data/plugins/cmd.py
   :language: python

.. _plugins/new:

Adding new plugins
------------------

More plugins can be added in :file:`~/.wiz/plugins` for development purpose. The
default plugins will always be loaded first, followed by the personal plugins.

A plugin is uniquely identified by the :attr:`IDENTIFIER` data string.
Therefore, you can overwrite a plugin by re-using the same identifier.

.. hint::

    It is highly recommended to deploy custom plugins when :ref:`installing
    <installing/source/options>` the package instead of using it from the
    personal plugin path as it can be error prone.

Adding new shells
~~~~~~~~~~~~~~~~~

Shells are just plugins that can be added. To select a different shell, edit the
``shell / type`` in the :ref:`configuration file <configuration>`.

# :coding: utf-8

import os

import docutils.nodes
import docutils.parsers.rst.directives
import sphinx.directives.code


class ExtendedCodeBlock(sphinx.directives.code.CodeBlock):
    """Code block directive with icon support.

    Example::

        .. extended-code-block::
            :icon: /image/prefer.png

            print "hello"

    """

    option_spec = {
        "linenos": docutils.parsers.rst.directives.flag,
        "emphasize-lines": docutils.parsers.rst.directives.unchanged_required,
        "icon": docutils.parsers.rst.directives.uri
    }

    def run(self):
        """Return nodes to represent directive."""
        nodes = super(ExtendedCodeBlock, self).run()

        # Wrap nodes in a new container and add icon if required.
        icon = self.options.get("icon")
        if icon:
            container = docutils.nodes.container(
                classes=["code-block-container"]
            )

            node = docutils.nodes.image(
                uri=icon, alt=os.path.splitext(os.path.basename(icon))[0]
            )
            node["classes"].append("icon")

            container.append(node)
            container.extend(nodes)

            nodes = [container]

        return nodes


def setup(app):
    """Setup plugin.

    Create ``extended-code-block`` directive with icon support.

    """
    app.add_directive("extended-code-block", ExtendedCodeBlock)

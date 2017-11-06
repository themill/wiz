# :coding: utf-8

"""Umwelt documentation build configuration file."""

import sys
import os
import re

# -- General ------------------------------------------------------------------
# Inject source onto path so that autodoc can find it by default, but in such a
# way as to allow overriding location.
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "source"))
)

# Extensions.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinxcontrib.autoprogram",
    "lowdown"
]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = u"Umwelt"
copyright = u"2017, The Mill"

# Version
with open(
    os.path.join(
        os.path.dirname(__file__), "..", "source",
        "umwelt", "_version.py"
    )
) as _version_file:
    _version = re.match(
        r".*__version__ = \"(.*?)\"", _version_file.read(), re.DOTALL
    ).group(1)

version = _version
release = _version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_template"]

# A list of prefixes to ignore for module listings.
modindex_common_prefix = [
    "umwelt."
]


# -- HTML output --------------------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

# If True, copy source rst files to output for reference.
html_copy_source = True


# -- Autodoc ------------------------------------------------------------------

autodoc_default_flags = ["members", "undoc-members", "inherited-members"]
autodoc_member_order = "bysource"


def autodoc_skip(app, what, name, obj, skip, options):
    """Don"t skip __init__ method for autodoc."""
    if name == "__init__":
        return False

    return skip


# -- Intersphinx --------------------------------------------------------------

intersphinx_mapping = {
    "python": ("http://docs.python.org/", None)
}


# -- Setup --------------------------------------------------------------------

def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip)


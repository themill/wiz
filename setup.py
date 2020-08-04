# :coding: utf-8

import collections
import os
import re

from setuptools import setup, find_packages
from setuptools.command.install import install

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
RESOURCE_PATH = os.path.join(ROOT_PATH, "resource")
SOURCE_PATH = os.path.join(ROOT_PATH, "source")
README_PATH = os.path.join(ROOT_PATH, "README.rst")

PACKAGE_NAME = "wiz"

# Read version from source.
with open(
    os.path.join(SOURCE_PATH, PACKAGE_NAME, "_version.py")
) as _version_file:
    VERSION = re.match(
        r".*__version__ = \"(.*?)\"", _version_file.read(), re.DOTALL
    ).group(1)

# Package required for the installation setup script to run.
SETUP_REQUIRES = [
    "toml >= 0.10.1, < 1"
]

# Compute dependencies.
INSTALL_REQUIRES = [
    "click >= 7, < 8",
    "colorama >= 0.3.9, < 1",
    "jsonschema >= 2.5, < 3",
    "packaging >= 17.1, < 18",
    "pystache >= 0.5.4, < 1",
    "sawmill >= 0.2.1, < 1",
    "toml >= 0.10.1, < 1"
]

DOC_REQUIRES = [
    "sphinx >= 1.8, < 2",
    "sphinx_rtd_theme >= 0.1.6, < 1",
    "lowdown >= 0.1.0, < 2",
    "sphinx-click >= 1.2.0"
]

TEST_REQUIRES = [
    "mock >= 2, < 3",
    "pytest-runner >= 2.7, < 3",
    "pytest >= 3.2.2, < 4",
    "pytest-mock >= 0.11, < 1",
    "pytest-xdist >= 1.1, < 2",
    "pytest-cov >= 2, < 3",
]


class InstallExtended(install):
    """Custom install command to set Wiz config."""

    # Extended options
    user_options = install.user_options + [
        ("wiz-config=", None, "TOML file to use as Wiz configuration.")
    ]

    # Path to initial Wiz config.
    wiz_config = None

    def finalize_options(self):
        """Sanitise optional argument to run installation command."""
        if self.wiz_config is not None:
            # Load configuration mapping from TOML file path.
            self.wiz_config = self._load_config(self.wiz_config)

        install.finalize_options(self)

    def run(self):
        """Run installation command."""
        import toml

        if self.wiz_config is not None:
            build_path = os.path.join(self.build_lib, PACKAGE_NAME)
            path = os.path.join(build_path, "package_data", "config.toml")
            data = self._load_config(path)

            # Update configuration data mapping with new config.
            data = self._deep_update(data, self.wiz_config)

            # Overwrite configuration file previously built.
            with open(path, "w") as stream:
                toml.dump(data, stream)

        install.run(self)

    def _deep_update(self, mapping1, mapping2):
        """Recursively update *mapping1* from *mapping2*."""
        for key, value in mapping2.items():
            if isinstance(value, collections.Mapping):
                mapping1[key] = self._deep_update(mapping1.get(key, {}), value)
            else:
                mapping1[key] = value
        return mapping1

    @staticmethod
    def _load_config(path):
        """Load configuration mapping from TOML file *path*."""
        import toml

        try:
            with open(path, "r") as stream:
                return toml.load(stream)

        except Exception:
            raise ValueError(
                "The Wiz configuration cannot be loaded from path: {}"
                .format(os.path.abspath(path))
            )


setup(
    name="wiz",
    version=VERSION,
    description="Environment management framework.",
    long_description=open(README_PATH).read(),
    url="https://github.com/themill/wiz",
    keywords="",
    author="The Mill",
    packages=find_packages(SOURCE_PATH),
    package_dir={
        "": "source"
    },
    include_package_data=True,
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    tests_require=TEST_REQUIRES,
    extras_require={
        "doc": DOC_REQUIRES,
        "test": TEST_REQUIRES,
        "dev": DOC_REQUIRES + TEST_REQUIRES
    },
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "wiz = wiz.__main__:main"
        ]
    },
    cmdclass={
        "install": InstallExtended,
    },
)

# :coding: utf-8

import os
import re
import shutil

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

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

# Compute dependencies.
INSTALL_REQUIRES = [
    "click >= 7, < 8",
    "coloredlogs >= 14.0, < 15",
    "colorama >= 0.3.9, < 1",
    "distro >= 1.5.0, < 2",
    "packaging >= 17.1, < 18",
    "six >= 1.15.0, < 2",
    "toml >= 0.10.1, < 1",
    "ujson >= 2.0.3, < 4"
]

DOC_REQUIRES = [
    "sphinx >= 1.8, < 2",
    "sphinx_rtd_theme >= 0.1.6, < 1",
    "lowdown >= 0.1.0, < 2",
    "sphinx-click >= 1.2.0"
]

TEST_REQUIRES = [
    "pytest >= 4, < 5",
    "pytest-benchmark >= 3.2.3, < 4",
    "pytest-cov >= 2, < 3",
    "pytest-mock >= 2, < 3",
    "pytest-runner >= 2.7, < 3",
    "pytest-xdist >= 1.18, < 2"
]

DEV_REQUIRES = [
    "versup >= 1.0.1",
]


class BuildExtended(build_py):
    """Custom command to build package with custom configuration and plugins."""

    # Extended options
    user_options = build_py.user_options + [
        (
            "wiz-config-file=", None,
            "Path to TOML file to embed in installed location as the default "
            "Wiz configuration."
        ),
        (
            "wiz-plugin-path=", None,
            "Path to directory containing Python Wiz plugins to embed in "
            "installed location."
        )
    ]

    # Initialize extended options.
    wiz_config_file = None
    wiz_plugin_path = None

    def run(self):
        """Run installation command."""
        build_py.run(self)

        build_path = os.path.join(self.build_lib, PACKAGE_NAME)
        config_path = os.path.join(build_path, "package_data", "config.toml")
        plugin_path = os.path.join(build_path, "package_data", "plugins")

        if self.wiz_config_file is not None:
            shutil.copy(self.wiz_config_file, config_path)

        if self.wiz_plugin_path is not None:
            for path in os.listdir(self.wiz_plugin_path):
                _path = os.path.join(self.wiz_plugin_path, path)
                shutil.copy(_path, plugin_path)


setup(
    name="wiz-env",
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
    install_requires=INSTALL_REQUIRES,
    tests_require=TEST_REQUIRES,
    extras_require={
        "doc": DOC_REQUIRES,
        "test": TEST_REQUIRES,
        "dev": DOC_REQUIRES + TEST_REQUIRES + DEV_REQUIRES
    },
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "wiz = wiz.__main__:main"
        ]
    },
    cmdclass={
        "build_py": BuildExtended,
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 "
        "(LGPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development",
    ],
)

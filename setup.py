# :coding: utf-8

import re
import os

from setuptools import setup, find_packages


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
    "mlog >= 0.0.6, < 1",
    "packaging >= 17.1, < 18",
    "jsonschema >= 2.5, < 3"
]

DOC_REQUIRES = [
    "sphinx >= 1.6, < 1.7",
    "sphinx_rtd_theme >= 0.1.6, < 1",
    "lowdown >= 0.1.0, < 2",

    # Restricted as 0.1.3 causes failed builds.
    # https://bitbucket.org/birkenfeld/sphinx-contrib/issues/168
    "sphinxcontrib-autoprogram >= 0.1.2, !=0.1.3, < 1"
]

TEST_REQUIRES = [
    "pytest-runner >= 2.7, < 3",
    "pytest >= 3.2.2, < 4",
    "pytest-mock >= 0.11, < 1",
    "pytest-xdist >= 1.1, < 2",
    "pytest-cov >= 2, < 3"
]


setup(
    name="wiz",
    version=VERSION,
    description="Package management system.",
    long_description=open(README_PATH).read(),
    url="http://gitlab/rnd/wiz",
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
        "dev": DOC_REQUIRES + TEST_REQUIRES
    },
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "wiz = wiz.__main__:main"
        ]
    },
)

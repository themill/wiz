# :coding: utf-8

import os

import pytest


@pytest.fixture()
def registry(temporary_directory):
    """Return a mocked registry path."""
    file_structure = {
        "envA/envA-0.2.0.json": (
            """
            {
                "identifier": "envA",
                "version": "0.2.0",
                "requirement": [
                    "envC >= 0.3.2, <1"
                ]
            }
            """
        ),
        "envA/envA-0.1.0.json": (
            """
            {
                "identifier": "envA",
                "version": "0.1.0"
            }
            """
        ),
        "envB/envB-0.1.0.json": (
            """
            {
                "identifier": "envB",
                "version": "0.1.0",
                "requirement": [
                    "envD >= 0.1.0",
                    "envF >= 1"
                ]
            }
            """
        ),
        "envC/envC-0.3.2.json": (
            """
            {
                "identifier": "envC",
                "version": "0.3.2",
                "requirement": [
                    "envD == 0.1.0"
                ]
            }
            """
        ),
        "envD/envD-0.1.1.json": (
            """
            {
                "identifier": "envD",
                "version": "0.1.1",
                "requirement": [
                    "envE >= 2"
                ]
            }
            """
        ),
        "envD/envD-0.1.0.json": (
            """
            {
                "identifier": "envD",
                "version": "0.1.0"
            }
            """
        ),
        "envE/envE-2.3.0.json": (
            """
            {
                "identifier": "envE",
                "version": "2.3.0",
                "requirement": [
                    "envF >= 0.2"
                ]
            }
            """
        ),
        "envF/envF-1.0.0.json": (
            """
            {
                "identifier": "envF",
                "version": "1.0.0"
            }
            """
        ),
        "envF/envF-0.2.0.json": (
            """
            {
                "identifier": "envF",
                "version": "0.2.0"
            }
            """
        ),
        "envG/envG-2.0.2.json": (
            """
            {
                "identifier": "envG",
                "version": "2.0.2",
                "requirement": [
                    "envB < 0.2.0"
                ]
            }
            """
        )
    }

    for path, content in file_structure.items():
        full_path = os.path.join(temporary_directory, path)
        repository = os.path.dirname(full_path)

        if not os.path.isdir(repository):
            os.makedirs(repository)

        with open(full_path, "w") as _file:
            _file.write(content.strip())

    return temporary_directory


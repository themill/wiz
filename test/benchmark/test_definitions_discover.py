# :coding: utf-8

import os
import uuid
import shutil
import tempfile

import ujson
import pytest

import wiz
import wiz.config


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


@pytest.fixture(scope="module")
def registries(request):
    """Return mocked registry paths with many definitions at several depths."""
    # Create registries
    registry_01 = tempfile.mkdtemp()
    registry_02 = tempfile.mkdtemp()
    registry_03 = tempfile.mkdtemp()

    # Define lots of environment variables for each definitions.
    environ = {
        "KEY{}".format(index): "VALUE{}".format(index)
        for index in range(100)
    }

    # Define lots of commands for each definitions.
    command = {
        "app{}".format(index): "App{}".format(index)
        for index in range(100)
    }

    # Define lots of requirements for each definitions.
    requirements = ["foo{}".format(index) for index in range(100)]

    # Define lots of variants for each definitions.
    variants = [
        {
            "identifier": "Variant{}".format(index),
            "requirements": ["bar{}".format(index) for index in range(100)],
            "environ": {
                "VAR_KEY{}".format(index): "VALUE{}".format(index)
                for index in range(100)
            }
        }
        for index in range(500)
    ]

    # All possible versions and system requirements.
    versions = ["0.1.0", "0.2.0", "1.0.0", "2.0.0", "2.0.0a", None]
    systems = [{"platform": "linux"}, {"platform": "windows"}]

    # Initialize identifier
    identifier = None

    for registry in [registry_01, registry_02, registry_03]:
        for index in range(1500):
            version = versions[index % len(versions)]
            system = systems[index % len(systems)]

            # Reset identifier each time version is None or each time version
            # cycle is re-initiated.
            if (
                identifier is None or version is None
                or not index % len(versions)
            ):
                identifier = str(uuid.uuid4())

            data = {
                "identifier": identifier,
                "system": system,
                "environ": environ,
                "command": command,
                "requirements": requirements,
                "variants": variants[:]
            }

            if version is not None:
                data["version"] = version

            # Write definition
            path = os.path.join(registry, identifier)
            file_path = os.path.join(path, "{}.json".format(identifier))

            if not os.path.isdir(path):
                os.makedirs(path)

            with open(file_path, "w") as stream:
                ujson.dumps(data, stream)

    def cleanup():
        """Remove temporary directories."""
        shutil.rmtree(registry_01)
        shutil.rmtree(registry_02)
        shutil.rmtree(registry_03)

    request.addfinalizer(cleanup)
    return [registry_01, registry_02, registry_03]


def test_discover_1500_definitions(registries, benchmark):
    """Test performance when fetching 1500 definitions in one registry."""
    benchmark(wiz.fetch_definition_mapping, registries[:1])


def test_discover_3000_definitions(registries, benchmark):
    """Test performance when fetching 3000 definitions in two registries."""
    benchmark(wiz.fetch_definition_mapping, registries[:2])


def test_discover_4500_definitions(registries, benchmark):
    """Test performance when fetching 4500 definitions in three registries."""
    benchmark(wiz.fetch_definition_mapping, registries)


def test_discover_4500_definitions_linux_only(registries, benchmark):
    """Test performance when fetching definitions for linux only."""
    benchmark(
        wiz.fetch_definition_mapping, registries,
        system_mapping={"platform": "linux"}
    )


def test_discover_4500_definitions_windows_only(registries, benchmark):
    """Test performance when fetching definitions for windows only."""
    benchmark(
        wiz.fetch_definition_mapping, registries,
        system_mapping={"platform": "windows"}
    )

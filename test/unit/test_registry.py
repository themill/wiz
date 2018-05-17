# :coding: utf-8

import os
import shutil
import pytest

import wiz.registry


@pytest.fixture()
def mocked_local_registry(mocker, temporary_directory):
    """Mocked the platform.system function."""
    path = os.path.join(temporary_directory, ".wiz", "registry")
    os.makedirs(path)
    mocker.patch.object(os.path, "expanduser", return_value=temporary_directory)
    return path


def test_get_local_reachable(mocked_local_registry):
    """Fail to return unreachable local registry."""
    assert wiz.registry.get_local() == mocked_local_registry


def test_get_local_unreachable(mocked_local_registry):
    """Return local registry."""
    shutil.rmtree(mocked_local_registry)
    assert wiz.registry.get_local() is None


def test_get_defaults():
    """Return default registries."""
    assert wiz.registry.get_defaults() == [
        os.path.join(
            os.sep, "mill3d", "server", "apps", "WIZ", "registry", "primary"
        ),
        os.path.join(
            os.sep, "mill3d", "server", "apps", "WIZ", "registry", "secondary"
        ),
        os.path.join(os.sep, "jobs", "ads", ".wiz", "registry")
    ]

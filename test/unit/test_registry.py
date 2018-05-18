# :coding: utf-8

import os
import os.path
import shutil
import types
import pytest

import wiz.registry
import wiz.filesystem


@pytest.fixture()
def mocked_accessible(mocker):
    """Mocked 'wiz.filesystem.is_accessible' function."""
    return mocker.patch.object(
        wiz.filesystem, "is_accessible", side_effect=[False, True, False, True]
    )


@pytest.fixture()
def mocked_local_registry(mocker, temporary_directory):
    """Return mocked local registry path."""
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
        os.path.join(os.sep, "jobs", ".common", "wiz", "registry")
    ]


def test_discover(mocked_accessible):
    """Discover registries under paths."""
    prefix = os.path.join(os.sep, "jobs", "ads")
    path = os.path.join(prefix, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    end = os.path.join(".common", "wiz", "registry")

    assert isinstance(registries, types.GeneratorType)
    assert list(registries) == [
        os.path.join(prefix, "project", "identity", end),
        os.path.join(prefix, "project", "identity", "shot", "animation", end)
    ]

    assert mocked_accessible.call_count == 4
    mocked_accessible.assert_any_call(
        os.path.join(prefix, "project", end),
    )
    mocked_accessible.assert_any_call(
        os.path.join(prefix, "project", "identity", end),
    )
    mocked_accessible.assert_any_call(
        os.path.join(prefix, "project", "identity", "shot", end),
    )
    mocked_accessible.assert_any_call(
        os.path.join(prefix, "project", "identity", "shot", "animation", end),
    )


def test_discover_fail(mocked_accessible):
    """Fail to discover registries under paths not in /jobs/ads."""
    prefix = os.path.join(os.sep, "somewhere", "else")
    path = os.path.join(prefix, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    assert isinstance(registries, types.GeneratorType)
    assert list(registries) == []

    mocked_accessible.assert_not_called()

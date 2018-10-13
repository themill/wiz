# :coding: utf-8

import os
import os.path
import types
import requests
import pwd
import getpass
import pytest

import wiz.registry
import wiz.filesystem


@pytest.fixture()
def mocked_accessible(mocker):
    """Return mocked 'wiz.filesystem.is_accessible' function."""
    return mocker.patch.object(wiz.filesystem, "is_accessible")


@pytest.fixture()
def mocked_user_home(mocker, temporary_directory):
    """Return mocked local home path."""
    mocker.patch.object(
        os.path, "expanduser", return_value=temporary_directory
    )
    return temporary_directory


@pytest.fixture()
def mocked_local(mocker):
    """Return mocked local registry path."""
    return mocker.patch.object(
        wiz.registry, "get_local", return_value="/usr/people/me/.wiz/registry"
    )


@pytest.fixture()
def mocked_discover(mocker):
    """Return mocked working directory registry paths."""
    paths = [
        "/jobs/ads/project/.common/wiz/registry",
        "/jobs/ads/project/identity/shot/.common/wiz/registry",
    ]
    return mocker.patch.object(
        wiz.registry, "discover", return_value=(path for path in paths)
    )


@pytest.fixture()
def mocked_requests_get(mocker):
    """Return mocked 'requests.get' function."""
    return mocker.patch.object(requests, "get")


@pytest.fixture()
def mocked_requests_post(mocker):
    """Return mocked 'requests.post' function."""
    return mocker.patch.object(requests, "post")


@pytest.fixture()
def mocked_requests_response(mocker):
    """Return mocked 'requests' response object."""
    return mocker.Mock()


@pytest.fixture()
def mocked_pwnam_response(mocker):
    """Return mocked 'getpwnam' object."""
    return mocker.Mock()


@pytest.fixture()
def mocked_pwnam(mocker):
    """Return mocked 'getpwnam' response object."""
    return mocker.patch.object(pwd, "getpwnam")


@pytest.fixture()
def mocked_getuser(mocker):
    """Return mocked 'getuser' response object."""
    return mocker.patch.object(getpass, "getuser")


@pytest.fixture()
def mocked_isdir(mocker):
    """Return mocked 'isdir' response object."""
    return mocker.patch.object(os.path, "isdir")


def test_get_local_reachable(mocked_user_home):
    """Fail to return unreachable local registry."""
    path = os.path.join(mocked_user_home, ".wiz", "registry")
    os.makedirs(path)
    assert wiz.registry.get_local() == path


@pytest.mark.usefixtures("mocked_user_home")
def test_get_local_unreachable():
    """Return local registry."""
    assert wiz.registry.get_local() is None


def test_get_defaults():
    """Return default registries."""
    assert wiz.registry.get_defaults() == [
        os.path.join(
            os.sep, "mill3d", "server", "apps", "WIZ", "registry",
            "primary", "default"
        ),
        os.path.join(
            os.sep, "mill3d", "server", "apps", "WIZ", "registry",
            "secondary", "default"
        ),
        os.path.join(os.sep, "jobs", ".wiz", "registry", "default")
    ]


def test_discover(mocked_accessible):
    """Discover registries under paths."""
    mocked_accessible.side_effect = [False, True, False, True]

    prefix = os.path.join(os.sep, "jobs", "ads")
    path = os.path.join(prefix, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    end = os.path.join(".wiz", "registry")

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
    mocked_accessible.side_effect = [False, True, False, True]

    prefix = os.path.join(os.sep, "somewhere", "else")
    path = os.path.join(prefix, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    assert isinstance(registries, types.GeneratorType)
    assert list(registries) == []

    mocked_accessible.assert_not_called()


@pytest.mark.parametrize("options, paths, expected", [
    (
        {},
        ["/path/to/registry1", "path/to/registry2"],
        [
            "/path/to/registry1",
            "path/to/registry2",
            "/jobs/ads/project/.common/wiz/registry",
            "/jobs/ads/project/identity/shot/.common/wiz/registry",
            "/usr/people/me/.wiz/registry"
        ]
    ),
    (
        {"include_local": False},
        ["/path/to/registry1", "path/to/registry2"],
        [
            "/path/to/registry1",
            "path/to/registry2",
            "/jobs/ads/project/.common/wiz/registry",
            "/jobs/ads/project/identity/shot/.common/wiz/registry"
        ]
    ),
    (
        {"include_working_directory": False},
        ["/path/to/registry1", "path/to/registry2"],
        [
            "/path/to/registry1",
            "path/to/registry2",
            "/usr/people/me/.wiz/registry"
        ]
    ),
    (
        {"include_local": False, "include_working_directory": False},
        ["/path/to/registry1", "path/to/registry2"],
        ["/path/to/registry1", "path/to/registry2"]
    )
], ids=[
    "default",
    "without-local",
    "without-cwd",
    "without-local-nor-cwd",
])
@pytest.mark.usefixtures("mocked_local")
@pytest.mark.usefixtures("mocked_discover")
def test_fetch(mocked_accessible, options, paths, expected):
    """Fetch the registries."""
    mocked_accessible.return_value = True
    assert wiz.registry.fetch(paths, **options) == expected


@pytest.mark.usefixtures("mocked_discover")
def test_fetch_unreachable_local(mocked_accessible, mocked_local):
    mocked_accessible.return_value = True
    mocked_local.return_value = None

    paths = ["/path/to/registry1", "path/to/registry2"]
    assert wiz.registry.fetch(paths) == [
        "/path/to/registry1",
        "path/to/registry2",
        "/jobs/ads/project/.common/wiz/registry",
        "/jobs/ads/project/identity/shot/.common/wiz/registry"
    ]


@pytest.mark.usefixtures("mocked_discover")
@pytest.mark.usefixtures("mocked_local")
def test_fetch_unreachable_paths(mocked_accessible):
    mocked_accessible.side_effect = [True, False]

    paths = ["/path/to/registry1", "path/to/registry2"]
    assert wiz.registry.fetch(paths) == [
        "/path/to/registry1",
        "/jobs/ads/project/.common/wiz/registry",
        "/jobs/ads/project/identity/shot/.common/wiz/registry",
        "/usr/people/me/.wiz/registry"
    ]


def test_install_filesystem(mocker, mocked_isdir):
    """Install a definition to a registry on the file system."""
    mocked_isdir.return_value = True
    mocked_export_definition = mocker.patch.object(wiz, "export_definition")

    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
    })
    wiz.registry.install(definition, "/registry_location")

    mocked_export_definition.assert_called_once_with(
        "/registry_location", definition, overwrite=False
    )


def test_install_repository(
    mocked_requests_get, mocked_requests_post, mocked_requests_response,
    mocked_isdir, mocked_getuser, mocked_pwnam, mocked_pwnam_response
):
    """Install a definition to a registry repository."""
    mocked_isdir.return_value = False

    mocked_requests_get.return_value = mocked_requests_response
    mocked_requests_response.ok = True
    mocked_requests_response.json.return_value = {
        "data": {
            "content": {
                "registry": {}
            }
        }}
    mocked_requests_post.return_value = mocked_requests_response

    mocked_getuser.return_value = "user"
    mocked_pwnam.return_value = mocked_pwnam_response
    mocked_pwnam_response.pw_name = "user"
    mocked_pwnam_response.pw_gecos = "User Name"

    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
    })
    wiz.registry.install(definition, "registry")

    mocked_requests_get.assert_called_once_with(
        "http://wiz.themill.com/api/registry/all"
    )
    mocked_requests_post.assert_called_once_with(
        "http://wiz.themill.com/api/registry/test/release",
        params={
            "overwrite": False
        },
        data={
            "content": definition.encode(),
            "message": "Add 'test' [0.1.0] to registry (user)\n\nauthor: User Name",
            "namespaces": "[]"
        }
    )

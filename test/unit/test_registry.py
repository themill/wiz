# :coding: utf-8

import os
import os.path
import types
import requests
import pytest

import wiz.registry
import wiz.filesystem
import wiz.exception


@pytest.fixture()
def mocked_filesystem_accessible(mocker):
    """Return mocked 'wiz.filesystem.is_accessible' function."""
    return mocker.patch.object(wiz.filesystem, "is_accessible")


@pytest.fixture()
def mocked_filesystem_get_name(mocker):
    """Return mocked 'wiz.filesystem.get_name' function."""
    return mocker.patch.object(wiz.filesystem, "get_name")


@pytest.fixture()
def mocked_filesystem_get_username(mocker):
    """Return mocked 'wiz.filesystem.get_username' function."""
    return mocker.patch.object(wiz.filesystem, "get_username")


@pytest.fixture()
def mocked_export_definition(mocker):
    """Return mocked 'wiz.export_definition' function."""
    return mocker.patch.object(wiz, "export_definition")


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
def mocked_definition():
    """Return mocked simple definition."""
    return wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
    })


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


def test_discover(mocked_filesystem_accessible):
    """Discover registries under paths."""
    mocked_filesystem_accessible.side_effect = [False, True, False, True]

    prefix = os.path.join(os.sep, "jobs", "ads")
    path = os.path.join(prefix, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    end = os.path.join(".wiz", "registry")

    assert isinstance(registries, types.GeneratorType)
    assert list(registries) == [
        os.path.join(prefix, "project", "identity", end),
        os.path.join(prefix, "project", "identity", "shot", "animation", end)
    ]

    assert mocked_filesystem_accessible.call_count == 4
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(prefix, "project", end),
    )
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(prefix, "project", "identity", end),
    )
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(prefix, "project", "identity", "shot", end),
    )
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(prefix, "project", "identity", "shot", "animation", end),
    )


def test_discover_fail(mocked_filesystem_accessible):
    """Fail to discover registries under paths not in /jobs/ads."""
    mocked_filesystem_accessible.side_effect = [False, True, False, True]

    prefix = os.path.join(os.sep, "somewhere", "else")
    path = os.path.join(prefix, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    assert isinstance(registries, types.GeneratorType)
    assert list(registries) == []

    mocked_filesystem_accessible.assert_not_called()


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
def test_fetch(mocked_filesystem_accessible, options, paths, expected):
    """Fetch the registries."""
    mocked_filesystem_accessible.return_value = True
    assert wiz.registry.fetch(paths, **options) == expected


@pytest.mark.usefixtures("mocked_discover")
def test_fetch_unreachable_local(mocked_filesystem_accessible, mocked_local):
    mocked_filesystem_accessible.return_value = True
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
def test_fetch_unreachable_paths(mocked_filesystem_accessible):
    mocked_filesystem_accessible.side_effect = [True, False]

    paths = ["/path/to/registry1", "path/to/registry2"]
    assert wiz.registry.fetch(paths) == [
        "/path/to/registry1",
        "/jobs/ads/project/.common/wiz/registry",
        "/jobs/ads/project/identity/shot/.common/wiz/registry",
        "/usr/people/me/.wiz/registry"
    ]


@pytest.mark.parametrize("options, export_options", [
    (
        {},
        {"overwrite": False}
    ),
    (
        {"overwrite": True},
        {"overwrite": True}
    ),
], ids=[
    "no-options",
    "with-overwrite",
])
def test_install_to_path(
    temporary_directory, mocked_definition, mocked_export_definition, logger,
    options, export_options
):
    """Install definition to path."""
    wiz.registry.install_to_path(
        mocked_definition, temporary_directory, **options
    )

    registry_path = os.path.join(temporary_directory, ".wiz", "registry")
    mocked_export_definition.assert_called_once_with(
        registry_path, mocked_definition, **export_options
    )
    logger.info.assert_called_once_with(
        "Successfully installed test-0.1.0 to registry '{}'."
        .format(registry_path)
    )


def test_install_to_path_with_full_registry_path(
    temporary_directory, mocked_definition, mocked_export_definition, logger,
):
    """Install definition to full registry path."""
    registry_path = os.path.join(temporary_directory, ".wiz", "registry")
    os.makedirs(registry_path)

    wiz.registry.install_to_path(mocked_definition, registry_path)

    mocked_export_definition.assert_called_once_with(
        registry_path, mocked_definition, overwrite=False
    )
    logger.info.assert_called_once_with(
        "Successfully installed test-0.1.0 to registry '{}'."
        .format(registry_path)
    )


def test_install_to_path_with_relative_path(
    temporary_directory, mocked_definition, mocked_export_definition, logger
):
    """Install definition to relative registry path."""
    path = os.path.join(temporary_directory, "path", "..", "foo")
    os.makedirs(path)

    wiz.registry.install_to_path(mocked_definition, path)

    registry_path = os.path.join(temporary_directory, "foo", ".wiz", "registry")
    mocked_export_definition.assert_called_once_with(
        registry_path, mocked_definition, overwrite=False
    )
    logger.info.assert_called_once_with(
        "Successfully installed test-0.1.0 to registry '{}'."
        .format(registry_path)
    )


def test_install_to_path_error_path(
    temporary_directory, mocked_definition, mocked_export_definition, logger
):
    """Fail to install definition when path is incorrect."""
    registry_path = os.path.join(temporary_directory, "somewhere")

    with pytest.raises(wiz.exception.InstallError) as error:
        wiz.registry.install_to_path(mocked_definition, registry_path)

    mocked_export_definition.assert_not_called()
    logger.info.assert_not_called()

    assert (
        "{!r} is not a valid registry directory.".format(registry_path)
    ) in str(error)


def test_install_to_path_error_definition_exists(
    temporary_directory, mocked_definition, mocked_export_definition, logger
):
    """Fail to install definition when definition exists."""
    mocked_export_definition.side_effect = wiz.exception.FileExists()

    with pytest.raises(wiz.exception.DefinitionExists) as error:
        wiz.registry.install_to_path(mocked_definition, temporary_directory)

    registry_path = os.path.join(temporary_directory, ".wiz", "registry")
    mocked_export_definition.assert_called_once_with(
        registry_path, mocked_definition, overwrite=False
    )
    logger.info.assert_not_called()

    assert "Definition 'test-0.1.0' already exists." in str(error)


@pytest.mark.parametrize("options, overwrite", [
    ({}, "false"),
    ({"overwrite": True}, "true"),
], ids=[
    "no-options",
    "with-overwrite",
])
def test_install_to_vault(
    mocked_requests_get, mocked_requests_post, mocked_definition,
    mocked_filesystem_get_name, mocked_filesystem_get_username, logger,
    monkeypatch, mocker, options, overwrite
):
    """Install definition to vault registry."""
    monkeypatch.setenv("WIZ_SERVER", "https://wiz.themill.com")
    reload(wiz.symbol)

    mocked_requests_get.return_value = mocker.Mock(
        ok=True, **{
            "json.return_value": {
                "data": {
                    "content": {
                        "registry-id": {
                            "identifier": "registry-id",
                            "description": "This is a registry",
                            "avatar_url": "/project/registry-id/avatar",
                        }
                    }
                }
            }
        }
    )
    mocked_requests_post.return_value = mocker.Mock(ok=True)
    mocked_filesystem_get_name.return_value = "John Doe"
    mocked_filesystem_get_username.return_value = "john-doe"

    wiz.registry.install_to_vault(mocked_definition, "registry-id", **options)

    mocked_requests_get.assert_called_once_with(
        "https://wiz.themill.com/api/registry/all"
    )

    mocked_requests_post.assert_called_once_with(
        "https://wiz.themill.com/api/registry/registry-id/release",
        params={"overwrite": overwrite},
        data={
            "content": mocked_definition.encode(),
            "message": (
                "Add 'test' [0.1.0] to registry (john-doe)"
                "\n\nauthor: John Doe"
            )
        }
    )

    mocked_filesystem_get_name.assert_called_once()
    mocked_filesystem_get_username.assert_called_once()

    logger.info.assert_called_once_with(
        "Successfully installed test-0.1.0 to registry 'registry-id'."
    )


@pytest.mark.parametrize("json_response, expected_error", [
    ({"error": {"message": "Oh Shit!"}}, "Oh Shit!"),
    ({}, "unknown"),
], ids=[
    "with-json-error",
    "without-json-error",
])
def test_install_to_vault_error_get(
    mocked_requests_get, mocked_requests_post, mocked_definition,
    mocked_filesystem_get_name, mocked_filesystem_get_username, logger,
    monkeypatch, mocker, json_response, expected_error
):
    """Fail to install definition when fetching process failed."""
    monkeypatch.setenv("WIZ_SERVER", "https://wiz.themill.com")
    reload(wiz.symbol)

    mocked_requests_get.return_value = mocker.Mock(
        ok=False, **{"json.return_value": json_response}
    )

    with pytest.raises(wiz.exception.InstallError) as error:
        wiz.registry.install_to_vault(mocked_definition, "registry-id")

    mocked_requests_get.assert_called_once_with(
        "https://wiz.themill.com/api/registry/all"
    )

    mocked_requests_post.assert_not_called()
    mocked_filesystem_get_name.assert_not_called()
    mocked_filesystem_get_username.assert_not_called()
    logger.info.assert_not_called()

    assert (
        "Vault registries could not be retrieved: {}".format(expected_error)
    ) in str(error)


@pytest.mark.parametrize("json_response", [
    {"data": {"content": {}}}, {}
], ids=[
    "with-json-error",
    "without-json-error",
])
def test_install_to_vault_error_incorrect_identifier(
    mocked_requests_get, mocked_requests_post, mocked_definition,
    mocked_filesystem_get_name, mocked_filesystem_get_username, logger,
    monkeypatch, mocker, json_response
):
    """Fail to install definition when registry identifier is incorrect."""
    monkeypatch.setenv("WIZ_SERVER", "https://wiz.themill.com")
    reload(wiz.symbol)

    mocked_requests_get.return_value = mocker.Mock(
        ok=True, **{"json.return_value": json_response}
    )

    with pytest.raises(wiz.exception.InstallError) as error:
        wiz.registry.install_to_vault(mocked_definition, "registry-id")

    mocked_requests_get.assert_called_once_with(
        "https://wiz.themill.com/api/registry/all"
    )

    mocked_requests_post.assert_not_called()
    mocked_filesystem_get_name.assert_not_called()
    mocked_filesystem_get_username.assert_not_called()
    logger.info.assert_not_called()

    assert "'registry-id' is not a valid registry" in str(error)


def test_install_to_vault_error_definition_exists(
    mocked_requests_get, mocked_requests_post, mocked_definition,
    mocked_filesystem_get_name, mocked_filesystem_get_username, logger,
    monkeypatch, mocker
):
    """Fail to install definition when definition exists."""
    monkeypatch.setenv("WIZ_SERVER", "https://wiz.themill.com")
    reload(wiz.symbol)

    mocked_requests_get.return_value = mocker.Mock(
        ok=True, **{
            "json.return_value": {
                "data": {
                    "content": {
                        "registry-id": {
                            "identifier": "registry-id",
                            "description": "This is a registry",
                            "avatar_url": "/project/registry-id/avatar",
                        }
                    }
                }
            }
        }
    )

    mocked_requests_post.return_value = mocker.Mock(ok=False, status_code=409)
    mocked_filesystem_get_name.return_value = "John Doe"
    mocked_filesystem_get_username.return_value = "john-doe"

    with pytest.raises(wiz.exception.DefinitionExists) as error:
        wiz.registry.install_to_vault(mocked_definition, "registry-id")

    mocked_requests_get.assert_called_once_with(
        "https://wiz.themill.com/api/registry/all"
    )

    mocked_requests_post.assert_called_once_with(
        "https://wiz.themill.com/api/registry/registry-id/release",
        params={"overwrite": "false"},
        data={
            "content": mocked_definition.encode(),
            "message": (
                "Add 'test' [0.1.0] to registry (john-doe)"
                "\n\nauthor: John Doe"
            )
        }
    )

    mocked_filesystem_get_name.assert_called_once()
    mocked_filesystem_get_username.assert_called_once()
    logger.info.assert_not_called()

    assert "Definition 'test-0.1.0' already exists." in str(error)


@pytest.mark.parametrize("json_response, expected_error", [
    ({"error": {"message": "Oh Shit!"}}, "Oh Shit!"),
    ({}, "unknown"),
], ids=[
    "with-json-error",
    "without-json-error",
])
def test_install_to_vault_error_post(
    mocked_requests_get, mocked_requests_post, mocked_definition,
    mocked_filesystem_get_name, mocked_filesystem_get_username, logger,
    monkeypatch, mocker, json_response, expected_error
):
    """Fail to install definition when release post failed."""
    monkeypatch.setenv("WIZ_SERVER", "https://wiz.themill.com")
    reload(wiz.symbol)

    mocked_requests_get.return_value = mocker.Mock(
        ok=True, **{
            "json.return_value": {
                "data": {
                    "content": {
                        "registry-id": {
                            "identifier": "registry-id",
                            "description": "This is a registry",
                            "avatar_url": "/project/registry-id/avatar",
                        }
                    }
                }
            }
        }
    )

    mocked_requests_post.return_value = mocker.Mock(
        ok=False, status_code=500, **{"json.return_value": json_response}
    )
    mocked_filesystem_get_name.return_value = "John Doe"
    mocked_filesystem_get_username.return_value = "john-doe"

    with pytest.raises(wiz.exception.InstallError) as error:
        wiz.registry.install_to_vault(mocked_definition, "registry-id")

    mocked_requests_get.assert_called_once_with(
        "https://wiz.themill.com/api/registry/all"
    )

    mocked_requests_post.assert_called_once_with(
        "https://wiz.themill.com/api/registry/registry-id/release",
        params={"overwrite": "false"},
        data={
            "content": mocked_definition.encode(),
            "message": (
                "Add 'test' [0.1.0] to registry (john-doe)"
                "\n\nauthor: John Doe"
            )
        }
    )

    mocked_filesystem_get_name.assert_called_once()
    mocked_filesystem_get_username.assert_called_once()
    logger.info.assert_not_called()

    assert (
        "Definition could not be installed to registry 'registry-id': "
        "{}".format(expected_error)
    ) in str(error)

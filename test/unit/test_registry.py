# :coding: utf-8

import os
import os.path
import types

import pytest

import wiz.config
import wiz.exception
import wiz.filesystem
import wiz.registry


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


@pytest.fixture()
def mocked_remove(mocker):
    """Return mocked 'os.remove' function."""
    return mocker.patch.object(os, "remove")


@pytest.fixture()
def mocked_export_definition(mocker):
    """Return mocked 'wiz.export_definition' function."""
    return mocker.patch.object(wiz, "export_definition")


@pytest.fixture()
def mocked_fetch_definition_mapping(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    return mocker.patch.object(wiz, "fetch_definition_mapping")


@pytest.fixture()
def mocked_fetch_definition(mocker):
    """Return mocked 'wiz.fetch_definition' function."""
    return mocker.patch.object(wiz, "fetch_definition")


@pytest.fixture()
def mocked_filesystem_accessible(mocker):
    """Return mocked 'wiz.filesystem.is_accessible' function."""
    return mocker.patch.object(wiz.filesystem, "is_accessible")


@pytest.fixture()
def mocked_filesystem_get_name(mocker):
    """Return mocked 'wiz.filesystem.get_name' function."""
    return mocker.patch.object(wiz.filesystem, "get_name")


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
def mocked_definitions():
    """Return mocked simple definition list."""
    return [
        wiz.definition.Definition({
            "identifier": "foo",
            "version": "0.1.0",
        }),
        wiz.definition.Definition({
            "identifier": "bar",
        }),
        wiz.definition.Definition({
            "identifier": "baz",
            "version": "2.5.1",
        }),
    ]


@pytest.mark.usefixtures("mocked_user_home")
def test_get_local_unreachable():
    """Return local registry."""
    assert wiz.registry.get_local() is None


def test_get_defaults():
    """Return default registries."""
    assert wiz.registry.get_defaults() == []


def test_discover(mocked_filesystem_accessible):
    """Discover registries under paths."""
    mocked_filesystem_accessible.side_effect = [False, True, False, True]

    path = os.path.join(os.sep, "project", "identity", "shot", "animation")
    registries = wiz.registry.discover(path)

    end = os.path.join(".wiz", "registry")

    assert isinstance(registries, types.GeneratorType)
    assert list(registries) == [
        os.path.join(os.sep, "project", "identity", end),
        os.path.join(os.sep, "project", "identity", "shot", "animation", end)
    ]

    assert mocked_filesystem_accessible.call_count == 4
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(os.sep, "project", end),
    )
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(os.sep, "project", "identity", end),
    )
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(os.sep, "project", "identity", "shot", end),
    )
    mocked_filesystem_accessible.assert_any_call(
        os.path.join(os.sep, "project", "identity", "shot", "animation", end),
    )


def test_discover_with_prefix(mocked_filesystem_accessible):
    """Discover registries under prefix."""
    mocked_filesystem_accessible.side_effect = [False, True, False, True]

    # Add prefix in config.
    prefix = os.path.join(os.sep, "jobs", "ads")
    config = wiz.config.fetch()
    config["registry"]["discovery_prefix"] = prefix

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


def test_discover_with_prefix_fail(mocked_filesystem_accessible):
    """Fail to discover registries under paths not in prefix"""
    mocked_filesystem_accessible.side_effect = [False, True, False, True]

    # Add prefix in config.
    prefix = os.path.join(os.sep, "jobs", "ads")
    config = wiz.config.fetch()
    config["registry"]["discovery_prefix"] = prefix

    path = os.path.join(
        os.sep, "somewhere", "else", "project", "identity", "shot", "animation"
    )
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
            os.path.join(os.getcwd(), "path/to/registry2"),
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
            os.path.join(os.getcwd(), "path/to/registry2"),
            "/jobs/ads/project/.common/wiz/registry",
            "/jobs/ads/project/identity/shot/.common/wiz/registry"
        ]
    ),
    (
        {"include_working_directory": False},
        ["/path/to/registry1", "path/to/registry2"],
        [
            "/path/to/registry1",
            os.path.join(os.getcwd(), "path/to/registry2"),
            "/usr/people/me/.wiz/registry"
        ]
    ),
    (
        {"include_local": False, "include_working_directory": False},
        ["/path/to/registry1", os.path.join(os.getcwd(), "path/to/registry2")],
        ["/path/to/registry1", os.path.join(os.getcwd(), "path/to/registry2")]
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
        os.path.join(os.getcwd(), "path/to/registry2"),
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


def test_install_to_path(
    temporary_directory, mocked_definitions, mocked_fetch_definition_mapping,
    mocked_fetch_definition, mocked_export_definition, mocked_remove, logger,
):
    """Install definitions to path."""
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_definition.side_effect = wiz.exception.RequestNotFound("Error")

    wiz.registry.install_to_path(
        mocked_definitions, temporary_directory
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        [temporary_directory]
    )

    assert mocked_fetch_definition.call_count == 3
    mocked_fetch_definition.assert_any_call("foo==0.1.0", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("bar", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("baz==2.5.1", "__MAPPING__")

    mocked_remove.assert_not_called()

    assert mocked_export_definition.call_count == 3
    mocked_export_definition.assert_any_call(
        temporary_directory, mocked_definitions[0], overwrite=True
    )
    mocked_export_definition.assert_any_call(
        temporary_directory, mocked_definitions[1], overwrite=True
    )
    mocked_export_definition.assert_any_call(
        temporary_directory, mocked_definitions[2], overwrite=True
    )

    logger.info.assert_called_once_with(
        "Successfully installed 3 definition(s) to registry '{}'."
        .format(temporary_directory)
    )


def test_install_to_path_with_relative_path(
    temporary_directory, mocked_definitions, mocked_fetch_definition_mapping,
    mocked_fetch_definition, mocked_export_definition, mocked_remove, logger,
):
    """Install definitions to relative registry path."""
    path = os.path.join(temporary_directory, "path", "..", "foo")
    os.makedirs(path)

    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_definition.side_effect = wiz.exception.RequestNotFound("Error")

    wiz.registry.install_to_path(
        mocked_definitions, path
    )

    registry_path = os.path.join(temporary_directory, "foo")
    mocked_fetch_definition_mapping.assert_called_once_with(
        [registry_path]
    )

    assert mocked_fetch_definition.call_count == 3
    mocked_fetch_definition.assert_any_call("foo==0.1.0", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("bar", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("baz==2.5.1", "__MAPPING__")

    mocked_remove.assert_not_called()

    assert mocked_export_definition.call_count == 3
    mocked_export_definition.assert_any_call(
        registry_path, mocked_definitions[0], overwrite=True
    )
    mocked_export_definition.assert_any_call(
        registry_path, mocked_definitions[1], overwrite=True
    )
    mocked_export_definition.assert_any_call(
        registry_path, mocked_definitions[2], overwrite=True
    )

    logger.info.assert_called_once_with(
        "Successfully installed 3 definition(s) to registry '{}'."
        .format(registry_path)
    )


def test_install_to_path_error_path(
    temporary_directory, mocked_definitions, mocked_fetch_definition_mapping,
    mocked_fetch_definition, mocked_export_definition, mocked_remove, logger,
):
    """Fail to install definitions when path is incorrect."""
    registry_path = os.path.join(temporary_directory, "somewhere")

    with pytest.raises(wiz.exception.InstallError) as error:
        wiz.registry.install_to_path(mocked_definitions, registry_path)

    mocked_remove.assert_not_called()
    mocked_fetch_definition_mapping.assert_not_called()
    mocked_fetch_definition.assert_not_called()
    mocked_export_definition.assert_not_called()
    logger.info.assert_not_called()

    assert (
        "{!r} is not a valid registry directory.".format(registry_path)
    ) in str(error)


def test_install_to_path_error_definition_exists(
    temporary_directory, mocked_definitions, mocked_fetch_definition_mapping,
    mocked_fetch_definition, mocked_export_definition, mocked_remove, logger,
):
    """Fail to install definitions when definition exists."""
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_definition.side_effect = [
        wiz.exception.RequestNotFound("Error"),
        wiz.definition.Definition({
            "identifier": "bar",
        }),
        wiz.definition.Definition({
            "identifier": "baz",
            "version": "2.5.1",
            "description": "test",
        }),
    ]

    with pytest.raises(wiz.exception.DefinitionsExist) as error:
        wiz.registry.install_to_path(mocked_definitions, temporary_directory)

    mocked_fetch_definition_mapping.assert_called_once_with(
        [temporary_directory]
    )

    assert mocked_fetch_definition.call_count == 3
    mocked_fetch_definition.assert_any_call("foo==0.1.0", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("bar", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("baz==2.5.1", "__MAPPING__")

    mocked_remove.assert_not_called()
    mocked_export_definition.assert_not_called()
    logger.info.assert_not_called()

    assert (
        "DefinitionsExist: 1 definition(s) already exist in registry."
    ) in str(error)


def test_install_to_path_overwrite(
    temporary_directory, mocked_definitions, mocked_fetch_definition_mapping,
    mocked_fetch_definition, mocked_export_definition, mocked_remove, logger,
):
    """Install definitions while overwriting existing definitions."""
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_definition.side_effect = [
        wiz.exception.RequestNotFound("Error"),
        wiz.definition.Definition(
            {"identifier": "bar"},
            path="/path/to/registry/bar/bar.json"
        ),
        wiz.definition.Definition(
            {
                "identifier": "baz",
                "version": "2.5.1",
                "description": "test",
            },
            path="/path/to/registry/baz/baz-2.5.1.json"
        ),
    ]

    wiz.registry.install_to_path(
        mocked_definitions, temporary_directory, overwrite=True
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        [temporary_directory]
    )

    assert mocked_fetch_definition.call_count == 3
    mocked_fetch_definition.assert_any_call("foo==0.1.0", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("bar", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("baz==2.5.1", "__MAPPING__")

    mocked_remove.assert_called_once_with(
        "/path/to/registry/baz/baz-2.5.1.json"
    )

    assert mocked_export_definition.call_count == 2
    mocked_export_definition.assert_any_call(
        temporary_directory, mocked_definitions[0], overwrite=True
    )
    mocked_export_definition.assert_any_call(
        "/path/to/registry/baz", mocked_definitions[2], overwrite=True
    )

    logger.info.assert_called_once_with(
        "Successfully installed 2 definition(s) to registry '{}'."
        .format(temporary_directory)
    )


def test_install_to_path_no_content(
    temporary_directory, mocked_definitions, mocked_fetch_definition_mapping,
    mocked_fetch_definition, mocked_export_definition, mocked_remove, logger,
):
    """Fail to install definitions when no new content available."""
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_definition.side_effect = mocked_definitions

    with pytest.raises(wiz.exception.InstallNoChanges) as error:
        wiz.registry.install_to_path(mocked_definitions, temporary_directory)

    mocked_fetch_definition_mapping.assert_called_once_with(
        [temporary_directory]
    )

    assert mocked_fetch_definition.call_count == 3
    mocked_fetch_definition.assert_any_call("foo==0.1.0", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("bar", "__MAPPING__")
    mocked_fetch_definition.assert_any_call("baz==2.5.1", "__MAPPING__")

    mocked_remove.assert_not_called()
    mocked_export_definition.assert_not_called()
    logger.info.assert_not_called()

    assert "InstallNoChanges: Nothing to install." in str(error)

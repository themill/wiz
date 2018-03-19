# :coding: utf-8

import itertools
import os

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

from wiz import __version__
import wiz.package
import wiz.definition
import wiz.exception


@pytest.fixture()
def mocked_definition_query(mocker):
    """Return mocked definition getter."""
    return mocker.patch.object(wiz.definition, "query")


@pytest.fixture()
def mocked_package(mocker):
    """Return mocked Package constructor."""
    return mocker.patch.object(wiz.package, "Package", return_value="PACKAGE")


def test_extract_without_variant(mocked_definition_query, mocked_package):
    """Extract one Package from definition."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.3.4",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        }
    })

    mocked_definition_query.return_value = definition

    requirement = Requirement("test")
    result = wiz.package.extract(requirement, {})
    mocked_definition_query.assert_called_once_with(requirement, {})

    mocked_package.assert_called_once_with(definition)
    assert result == ["PACKAGE"]


def test_extract_with_all_variants(mocked_definition_query, mocked_package):
    """Extract all variant Packages from definition."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.3.4",
        "variants": [
            {
                "identifier": "Variant1",
                "environ": {"KEY1": "VALUE1"}
            },
            {
                "identifier": "Variant2",
                "environ": {"KEY2": "VALUE2"}
            },
            {
                "identifier": "Variant3",
                "environ": {"KEY3": "VALUE3"}
            }
        ]
    })

    mocked_definition_query.return_value = definition

    requirement = Requirement("test")
    result = wiz.package.extract(requirement, {})
    mocked_definition_query.assert_called_once_with(requirement, {})

    assert mocked_package.call_count == 3
    mocked_package.assert_any_call(definition, {
        "identifier": "Variant1",
        "environ": {"KEY1": "VALUE1"}
    })
    mocked_package.assert_any_call(definition, {
        "identifier": "Variant2",
        "environ": {"KEY2": "VALUE2"}
    })
    mocked_package.assert_any_call(definition, {
        "identifier": "Variant3",
        "environ": {"KEY3": "VALUE3"}
    })

    assert result == ["PACKAGE", "PACKAGE", "PACKAGE"]


def test_extract_with_one_requested_variant(
    mocked_definition_query, mocked_package
):
    """Extract one requested variant Package from definition."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.3.4",
        "variants": [
            {
                "identifier": "Variant1",
                "environ": {"KEY1": "VALUE1"}
            },
            {
                "identifier": "Variant2",
                "environ": {"KEY2": "VALUE2"}
            },
            {
                "identifier": "Variant3",
                "environ": {"KEY3": "VALUE3"}
            }
        ]
    })

    mocked_definition_query.return_value = definition

    requirement = Requirement("test[Variant2]")
    result = wiz.package.extract(requirement, {})
    mocked_definition_query.assert_called_once_with(requirement, {})

    mocked_package.assert_called_once_with(definition, {
        "identifier": "Variant2",
        "environ": {"KEY2": "VALUE2"}
    })

    assert result == ["PACKAGE"]


def test_extract_error(mocked_definition_query, mocked_package):
    """Fail to extract Package from definition."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.3.4",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        }
    })

    mocked_definition_query.return_value = definition

    requirement = Requirement("env1[Incorrect]")

    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.package.extract(requirement, {})

    mocked_definition_query.assert_called_once_with(requirement, {})
    mocked_package.assert_not_called()

    assert (
        "The variant 'Incorrect' could not been resolved "
        "for 'test' [0.3.4]." in str(error)
    )


@pytest.fixture()
def mocked_combine_environ(mocker):
    """Return mocked combine_environ_mapping function."""
    return mocker.patch.object(
        wiz.package, "combine_environ_mapping", return_value={"KEY": "VALUE"}
    )


@pytest.fixture()
def mocked_combine_command(mocker):
    """Return mocked combine_command_mapping function."""
    return mocker.patch.object(
        wiz.package, "combine_command_mapping", return_value={"APP": "APP_EXE"}
    )


@pytest.fixture()
def mocked_sanitise_environ(mocker):
    """Return mocked sanitise_environ_mapping function."""
    return mocker.patch.object(
        wiz.package, "sanitise_environ_mapping",
        return_value={"CLEAN_KEY": "CLEAN_VALUE"}
    )


def test_extract_context_without_packages(
    mocked_combine_environ, mocked_combine_command, mocked_sanitise_environ
):
    """Extract context with no packages."""
    assert wiz.package.extract_context([]) == {
        "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_not_called()
    mocked_combine_command.assert_not_called()
    mocked_sanitise_environ.assert_called_once_with({})


def test_extract_context_with_empty_package(
    mocked_combine_environ, mocked_combine_command, mocked_sanitise_environ
):
    """Extract context with package without environ nor command."""
    definition = wiz.definition.Definition({"identifier": "test"})
    packages = [wiz.package.Package(definition)]

    assert wiz.package.extract_context(packages) == {
        "command": {"APP": "APP_EXE"}, "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_called_once_with("test==unknown", {}, {})
    mocked_combine_command.assert_called_once_with("test==unknown", {}, {})
    mocked_sanitise_environ.assert_called_once_with({"KEY": "VALUE"})


def test_extract_context_with_one_package(
    mocked_combine_environ, mocked_combine_command, mocked_sanitise_environ
):
    """Extract context with one package."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "environ": {"key1": "value1"},
        "command": {"app": "App"}
    })
    packages = [wiz.package.Package(definition)]

    assert wiz.package.extract_context(packages) == {
        "command": {"APP": "APP_EXE"}, "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_called_once_with(
        "test==unknown", {}, {"key1": "value1"}
    )
    mocked_combine_command.assert_called_once_with(
        "test==unknown", {}, {"app": "App"}
    )
    mocked_sanitise_environ.assert_called_once_with({"KEY": "VALUE"})


def test_extract_context_with_five_package(
    mocked_combine_environ, mocked_combine_command, mocked_sanitise_environ
):
    """Extract context with five packages."""
    definitions = [
        wiz.definition.Definition({
            "identifier": "test1",
            "version": "0.1.0",
            "environ": {"key1": "value1"}}
        ),
        wiz.definition.Definition({
            "identifier": "test2",
            "command": {"app1": "App1"},
            "environ": {"key2": "value2"}
        }),
        wiz.definition.Definition({
            "identifier": "test3",
            "version": "3.1.2",
            "command": {"app2": "App2"},
            "environ": {"key3": "value3"}
        }),
        wiz.definition.Definition({
            "identifier": "test4",
            "version": "0.11.2",
            "environ": {"key4": "value4"}
        }),
        wiz.definition.Definition({
            "identifier": "test5",
            "version": "30",
            "command": {"app1": "AppX"},
            "environ": {"key5": "value5"}
        })
    ]

    packages = [wiz.package.Package(definition) for definition in definitions]

    assert wiz.package.extract_context(packages) == {
        "command": {"APP": "APP_EXE"}, "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }

    assert mocked_combine_environ.call_count == 5
    mocked_combine_environ.assert_any_call(
        "test1==0.1.0", {}, {"key1": "value1"}
    )
    mocked_combine_environ.assert_any_call(
        "test2==unknown", {"KEY": "VALUE"}, {"key2": "value2"}
    )
    mocked_combine_environ.assert_any_call(
        "test3==3.1.2", {"KEY": "VALUE"}, {"key3": "value3"}
    )
    mocked_combine_environ.assert_any_call(
        "test4==0.11.2", {"KEY": "VALUE"}, {"key4": "value4"}
    )
    mocked_combine_environ.assert_any_call(
        "test5==30", {"KEY": "VALUE"}, {"key5": "value5"}
    )

    assert mocked_combine_command.call_count == 5
    mocked_combine_command.assert_any_call(
        "test1==0.1.0", {}, {}
    )
    mocked_combine_command.assert_any_call(
        "test2==unknown", {"APP": "APP_EXE"}, {"app1": "App1"}
    )
    mocked_combine_command.assert_any_call(
        "test3==3.1.2", {"APP": "APP_EXE"}, {"app2": "App2"}
    )
    mocked_combine_command.assert_any_call(
        "test4==0.11.2", {"APP": "APP_EXE"}, {}
    )
    mocked_combine_command.assert_any_call(
        "test5==30", {"APP": "APP_EXE"}, {"app1": "AppX"}
    )

    mocked_sanitise_environ.assert_called_once_with({"KEY": "VALUE"})


@pytest.mark.usefixtures("mocked_combine_command")
@pytest.mark.usefixtures("mocked_sanitise_environ")
def test_extract_context_with_initial_data(mocked_combine_environ):
    """Return extracted context with initial environ mapping."""
    definitions = [
        wiz.definition.Definition({
            "identifier": "test1",
            "version": "0.1.0",
            "environ": {"key1": "value1"}}
        ),
        wiz.definition.Definition({
            "identifier": "test2",
            "command": {"app1": "App1"},
            "environ": {"key2": "value2"}
        }),
        wiz.definition.Definition({
            "identifier": "test3",
            "version": "3.1.2",
            "command": {"app2": "App2"},
            "environ": {"key3": "value3"}
        }),
    ]

    packages = [wiz.package.Package(definition) for definition in definitions]

    assert wiz.package.extract_context(
        packages, environ_mapping={"INITIAL_KEY": "INITIAL_VALUE"}
    ) == {
        "command": {"APP": "APP_EXE"},
        "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }

    mocked_combine_environ.assert_any_call(
        "test1==0.1.0", {"INITIAL_KEY": "INITIAL_VALUE"}, {"key1": "value1"}
    )


def test_sanitise_environ_mapping():
    """Return sanitised environment mapping"""
    assert wiz.package.sanitise_environ_mapping({
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2:${PLUGINS_A}",
        "PLUGINS_B": "${PLUGINS_B}:/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:${PLUGINS_C}:/path/to/plugin2",
        "KEY1": "HELLO",
        "KEY2": "${KEY1} WORLD!",
        "KEY3": "${UNKNOWN}"
    }) == {
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_B": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:/path/to/plugin2",
        "KEY1": "HELLO",
        "KEY2": "HELLO WORLD!",
        "KEY3": "${UNKNOWN}"
    }


@pytest.mark.parametrize("mapping1, mapping2, expected, warning", [
    (
        {"KEY": "HELLO"},
        {"KEY": "${KEY} WORLD!"},
        {"KEY": "HELLO WORLD!"},
        None
    ),
    (
        {"KEY": "VALUE1"},
        {"KEY": "VALUE2"},
        {"KEY": "VALUE2"},
        "The 'KEY' variable is being overridden in '{package}'"
    ),
    (
        {"PLUGIN": "/path/to/settings", "HOME": "/usr/people/me"},
        {"PLUGIN": "${HOME}/.app:${PLUGIN}"},
        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/settings"
        },
        None
    )
], ids=[
    "combine-key",
    "override-key",
    "mixed-combination"
])
def test_combine_environ_mapping(logger, mapping1, mapping2, expected, warning):
    """Return combined environment mapping from *mapping1* and *mapping2*."""
    package_identifier = "Test==0.1.0"
    assert wiz.package.combine_environ_mapping(
        package_identifier, mapping1, mapping2
    ) == expected

    if warning is None:
        logger.warning.assert_not_called()
    else:
        logger.warning.assert_called_once_with(
            warning.format(package=package_identifier)
        )


@pytest.mark.parametrize("mapping1, mapping2, expected, warning", [
    (
        {"app1": "App1"},
        {"app2": "App2"},
        {"app1": "App1", "app2": "App2"},
        None
    ),
    (
        {"app1": "App1.0"},
        {"app1": "App1.5"},
        {"app1": "App1.5"},
        "The 'app1' command is being overridden in '{package}'"
    )
], ids=[
    "combine-key",
    "override-key",
])
def test_combine_command_mapping(logger, mapping1, mapping2, expected, warning):
    """Return combined command mapping from *mapping1* and *mapping2*."""
    package_identifier = "Test==0.1.0"
    assert wiz.package.combine_command_mapping(
        package_identifier, mapping1, mapping2
    ) == expected

    if warning is None:
        logger.warning.assert_not_called()
    else:
        logger.warning.assert_called_once_with(
            warning.format(package=package_identifier)
        )


def test_minimal_package_without_variant():
    """Create minimal package instance created with no variant."""
    definition = wiz.definition.Definition({"identifier": "test"})

    package = wiz.package.Package(definition)
    assert package.identifier == "test==unknown"
    assert package.definition == definition
    assert package.description == "unknown"
    assert package.command == {}
    assert package.environ == {}
    assert package.requirements == []

    assert len(package) == 3
    assert sorted(package) == ["definition", "identifier", "variant_name"]


def test_full_package_without_variant():
    """Create full package instance created with no variant."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.3.4",
        "description": "Test definition",
        "command": {
            "app1": "App1",
            "app2": "App2",
        },
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        },
        "requirements": [
            "test1 >= 2",
            "test2"
        ]
    })

    package = wiz.package.Package(definition)
    assert package.identifier == "test==0.3.4"
    assert package.description == "Test definition"
    assert package.command == {"app1": "App1", "app2": "App2"}
    assert package.environ == {"KEY1": "VALUE1", "KEY2": "VALUE2"}

    for requirement_data, requirement in itertools.izip_longest(
        definition.get("requirements"), package.requirements
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(requirement_data))


def test_package_with_variant(mocked_combine_environ, mocked_combine_command):
    """Create full package instance created with no variant."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "command": {
            "app": "App",
        },
        "environ": {
            "A_KEY": "A_VALUE",
        },
        "requirements": [
            "test1 >= 2",
            "test2"
        ],
        "variants": [
            {
                "identifier": "Variant1",
                "environ": {
                    "KEY1": "VALUE1",
                },
                "requirements": [
                    "test3 >= 1.0, < 2"
                ]
            },
        ]
    })

    package = wiz.package.Package(
        definition, variant=definition.variants[0]
    )
    assert package.identifier == "test[Variant1]==0.1.0"
    assert package.version == Version("0.1.0")
    assert package.description == "This is a definition"
    assert package.command == {"APP": "APP_EXE"}
    assert package.environ == {"KEY": "VALUE"}

    for requirement_data, requirement in itertools.izip_longest(
        ["test1 >= 2", "test2", "test3 >= 1.0, < 2"], package.requirements
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(requirement_data))

    mocked_combine_environ.assert_called_once_with(
        "test[Variant1]==0.1.0",
        {"A_KEY": "A_VALUE"},
        {"KEY1": "VALUE1"}
    )

    mocked_combine_command.assert_called_once_with(
        "test[Variant1]==0.1.0",
        {"app": "App"},
        {}
    )


def test_initiate_data(monkeypatch):
    """Return initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")

    assert wiz.package.initiate_environ() == {
        "WIZ_VERSION": __version__,
        "USER": "someone",
        "LOGNAME": "someone",
        "HOME": "/path/to/somewhere",
        "DISPLAY": "localhost:0.0",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }


def test_initiate_data_with_initial_data(monkeypatch):
    """Return initial data mapping with initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")

    assert wiz.package.initiate_environ(
        mapping={
            "LOGNAME": "someone-else",
            "KEY": "VALUE"
        }
    ) == {
        "WIZ_VERSION": __version__,
        "USER": "someone",
        "LOGNAME": "someone-else",
        "HOME": "/path/to/somewhere",
        "DISPLAY": "localhost:0.0",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ]),
        "KEY": "VALUE"
    }

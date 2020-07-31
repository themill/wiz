# :coding: utf-8

import copy

import pytest

import wiz.definition
import wiz.environ
import wiz.exception
import wiz.package
from wiz.utility import Requirement, Version


@pytest.fixture()
def mocked_definition_query(mocker):
    """Return mocked definition getter."""
    return mocker.patch.object(wiz.definition, "query")


@pytest.fixture()
def mocked_package(mocker):
    """Return mocked Package constructor."""
    return mocker.patch.object(wiz.package, "Package", return_value="PACKAGE")


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_without_variant(
    mocked_definition_query, mocked_package, kwargs, namespace_counter
):
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
    result = wiz.package.extract(requirement, {}, **kwargs)
    mocked_definition_query.assert_called_once_with(
        requirement, {}, namespace_counter=namespace_counter
    )

    mocked_package.assert_called_once_with({
        "identifier": "test==0.3.4",
        "definition": definition,
        "version": Version("0.3.4"),
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2"
        }
    })
    assert result == ["PACKAGE"]


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_with_all_variants(
    mocked_definition_query, mocked_package, kwargs, namespace_counter
):
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
    result = wiz.package.extract(requirement, {}, **kwargs)
    mocked_definition_query.assert_called_once_with(
        requirement, {}, namespace_counter=namespace_counter
    )

    assert mocked_package.call_count == 3
    mocked_package.assert_any_call({
        "identifier": "test[Variant1]==0.3.4",
        "definition": definition,
        "version": Version("0.3.4"),
        "variant-name": "Variant1",
        "environ": {"KEY1": "VALUE1"}
    })

    mocked_package.assert_any_call({
        "identifier": "test[Variant2]==0.3.4",
        "definition": definition,
        "version": Version("0.3.4"),
        "variant-name": "Variant2",
        "environ": {"KEY2": "VALUE2"}
    })

    mocked_package.assert_any_call({
        "identifier": "test[Variant3]==0.3.4",
        "definition": definition,
        "version": Version("0.3.4"),
        "variant-name": "Variant3",
        "environ": {"KEY3": "VALUE3"}
    })

    assert result == ["PACKAGE", "PACKAGE", "PACKAGE"]


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_with_one_requested_variant(
    mocked_definition_query, mocked_package, kwargs, namespace_counter
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
    result = wiz.package.extract(requirement, {}, **kwargs)
    mocked_definition_query.assert_called_once_with(
        requirement, {}, namespace_counter=namespace_counter
    )

    mocked_package.assert_called_once_with({
        "identifier": "test[Variant2]==0.3.4",
        "definition": definition,
        "version": Version("0.3.4"),
        "variant-name": "Variant2",
        "environ": {"KEY2": "VALUE2"}
    })

    assert result == ["PACKAGE"]


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_error(
    mocked_definition_query, mocked_package, kwargs, namespace_counter
):
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
        wiz.package.extract(requirement, {}, **kwargs)

    mocked_definition_query.assert_called_once_with(
        requirement, {}, namespace_counter=namespace_counter
    )
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
def mocked_environ_sanitise(mocker):
    """Return mocked 'wiz.environ.sanitise' function."""
    return mocker.patch.object(
        wiz.environ, "sanitise", return_value={"CLEAN_KEY": "CLEAN_VALUE"}
    )


def test_extract_context_without_packages(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitise
):
    """Extract context with no packages."""
    assert wiz.package.extract_context([]) == {
        "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_not_called()
    mocked_combine_command.assert_not_called()
    mocked_environ_sanitise.assert_called_once_with({})


def test_extract_context_with_empty_package(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitise
):
    """Extract context with package without environ nor command."""
    definition = wiz.definition.Definition({"identifier": "test"})
    packages = [wiz.package.Package(definition)]

    assert wiz.package.extract_context(packages) == {
        "command": {"APP": "APP_EXE"}, "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_called_once_with("test", {}, {})
    mocked_combine_command.assert_called_once_with("test", {}, {})
    mocked_environ_sanitise.assert_called_once_with({"KEY": "VALUE"})


def test_extract_context_with_one_package(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitise
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
        "test", {}, {"key1": "value1"}
    )
    mocked_combine_command.assert_called_once_with(
        "test", {}, {"app": "App"}
    )
    mocked_environ_sanitise.assert_called_once_with({"KEY": "VALUE"})


def test_extract_context_with_six_package(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitise
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
            "install-location": "/path/to/package",
            "command": {"app1": "AppX"},
            "environ": {"PATH": "${INSTALL_LOCATION}/bin"}
        }),
        wiz.definition.Definition({
            "identifier": "test6",
            "version": "30.5",
            "install-location": "/path/to/package",
            "command": {"app1": "AppX"},
            "environ": {"PATH": "${INSTALL_LOCATION}/bin"}
        })
    ]

    packages = [wiz.package.create(definition) for definition in definitions]

    assert wiz.package.extract_context(packages) == {
        "command": {"APP": "APP_EXE"}, "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }

    assert mocked_combine_environ.call_count == 6
    mocked_combine_environ.assert_any_call(
        "test1==0.1.0", {}, {"key1": "value1"}
    )
    mocked_combine_environ.assert_any_call(
        "test2", {"KEY": "VALUE"}, {"key2": "value2"}
    )
    mocked_combine_environ.assert_any_call(
        "test3==3.1.2", {"KEY": "VALUE"}, {"key3": "value3"}
    )
    mocked_combine_environ.assert_any_call(
        "test4==0.11.2", {"KEY": "VALUE"}, {"key4": "value4"}
    )
    mocked_combine_environ.assert_any_call(
        "test5==30", {"KEY": "VALUE"}, {"PATH": "/path/to/package/bin"}
    )
    mocked_combine_environ.assert_any_call(
        "test6==30.5", {"KEY": "VALUE"}, {"PATH": "/path/to/package/bin"}
    )

    assert mocked_combine_command.call_count == 6
    mocked_combine_command.assert_any_call(
        "test1==0.1.0", {}, {}
    )
    mocked_combine_command.assert_any_call(
        "test2", {"APP": "APP_EXE"}, {"app1": "App1"}
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
    mocked_combine_command.assert_any_call(
        "test6==30.5", {"APP": "APP_EXE"}, {"app1": "AppX"}
    )

    mocked_environ_sanitise.assert_called_once_with({"KEY": "VALUE"})


@pytest.mark.usefixtures("mocked_combine_command")
@pytest.mark.usefixtures("mocked_environ_sanitise")
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

    packages = [wiz.package.create(definition) for definition in definitions]

    assert wiz.package.extract_context(
        packages, environ_mapping={"INITIAL_KEY": "INITIAL_VALUE"}
    ) == {
        "command": {"APP": "APP_EXE"},
        "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }

    mocked_combine_environ.assert_any_call(
        "test1==0.1.0", {"INITIAL_KEY": "INITIAL_VALUE"}, {"key1": "value1"}
    )


@pytest.mark.parametrize("mapping1, mapping2, expected, warning", [
    (
        {"KEY": "HELLO"},
        {"KEY": "${KEY} WORLD!"},
        {"KEY": "HELLO WORLD!"},
        None
    ),
    (
        {"KEY": "HELLO"},
        {"KEY": "$KEY WORLD!"},
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
    ),
    (
        {"PLUGIN": "/path/to/settings", "HOME": "/usr/people/me"},
        {"PLUGIN": "$HOME/.app:$PLUGIN"},
        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/settings"
        },
        None
    )
], ids=[
    "combine-key",
    "combine-key-without-curly-brackets",
    "override-key",
    "mixed-combination",
    "mixed-combination-without-curly-brackets"
])
def test_combine_environ_mapping(logger, mapping1, mapping2, expected, warning):
    """Return combined environment mapping from *mapping1* and *mapping2*."""
    package_identifier = "Test==0.1.0"

    result = wiz.package.combine_environ_mapping(
        package_identifier, mapping1, mapping2
    )
    assert result == expected

    if warning is None:
        logger.warning.assert_not_called()
    else:
        logger.warning.assert_called_once_with(
            warning.format(package=package_identifier)
        )


@pytest.mark.parametrize("mapping1, mapping2, expected", [
    (
        {"app1": "App1"},
        {"app2": "App2"},
        {"app1": "App1", "app2": "App2"},
    ),
    (
        {"app1": "App1.0"},
        {"app1": "App1.5"},
        {"app1": "App1.5"},
    )
], ids=[
    "combine-key",
    "override-key",
])
def test_combine_command_mapping(mapping1, mapping2, expected):
    """Return combined command mapping from *mapping1* and *mapping2*."""
    package_identifier = "Test==0.1.0"
    assert wiz.package.combine_command_mapping(
        package_identifier, mapping1, mapping2
    ) == expected


def test_package_mapping():
    """Create package and return mapping and serialized mapping."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "registry": "/registry",
        "definition-location": "/registry/test-0.1.0.json",
        "auto-use": True,
        "system": {
            "platform": "linux",
            "os": "el >= 6, < 7",
            "arch": "x86_64"
        },
        "variants": [
            {
                "identifier": "V1",
                "command": {
                    "app": "AppX"
                },
                "environ": {
                    "KEY1": "VALUE1"
                },
                "requirements": ["foo"]
            }
        ]
    })

    data = {
        "identifier": "test[V1]==0.1.0",
        "version": "0.1.0",
        "definition": definition,
        "variant-name": "V1",
        "description": "This is a definition",
        "registry": "/registry",
        "definition-location": "/registry/test-0.1.0.json",
        "auto-use": True,
        "system": {
            "platform": "linux",
            "os": "el >= 6, < 7",
            "arch": "x86_64"
        },
        "command": {
            "app": "AppX"
        },
        "environ": {
            "KEY1": "VALUE1"
        },
        "requirements": ["foo"]
    }

    environment = wiz.package.Package(data)

    assert environment.to_dict() == {
        "identifier": "test[V1]==0.1.0",
        "version": Version("0.1.0"),
        "definition": definition,
        "variant-name": "V1",
        "description": "This is a definition",
        "registry": "/registry",
        "definition-location": "/registry/test-0.1.0.json",
        "auto-use": True,
        "system": {
            "platform": "linux",
            "os": "el >= 6, < 7",
            "arch": "x86_64"
        },
        "command": {
            "app": "AppX"
        },
        "environ": {
            "KEY1": "VALUE1"
        },
        "requirements": [Requirement("foo")]
    }

    assert environment.encode() == (
        "{\n"
        "    \"identifier\": \"test[V1]==0.1.0\",\n"
        "    \"definition\": {\n"
        "        \"identifier\": \"test\",\n"
        "        \"version\": \"0.1.0\",\n"
        "        \"description\": \"This is a definition\",\n"
        "        \"registry\": \"/registry\",\n"
        "        \"definition-location\": \"/registry/test-0.1.0.json\",\n"
        "        \"auto-use\": true,\n"
        "        \"system\": {\n"
        "            \"platform\": \"linux\",\n"
        "            \"os\": \"el >= 6, < 7\",\n"
        "            \"arch\": \"x86_64\"\n"
        "        },\n"
        "        \"variants\": [\n"
        "            {\n"
        "                \"identifier\": \"V1\",\n"
        "                \"command\": {\n"
        "                    \"app\": \"AppX\"\n"
        "                },\n"
        "                \"environ\": {\n"
        "                    \"KEY1\": \"VALUE1\"\n"
        "                },\n"
        "                \"requirements\": [\n"
        "                    \"foo\"\n"
        "                ]\n"
        "            }\n"
        "        ]\n"
        "    },\n"
        "    \"variant-name\": \"V1\",\n"
        "    \"version\": \"0.1.0\",\n"
        "    \"description\": \"This is a definition\",\n"
        "    \"registry\": \"/registry\",\n"
        "    \"definition-location\": \"/registry/test-0.1.0.json\",\n"
        "    \"auto-use\": true,\n"
        "    \"system\": {\n"
        "        \"platform\": \"linux\",\n"
        "        \"os\": \"el >= 6, < 7\",\n"
        "        \"arch\": \"x86_64\"\n"
        "    },\n"
        "    \"command\": {\n"
        "        \"app\": \"AppX\"\n"
        "    },\n"
        "    \"environ\": {\n"
        "        \"KEY1\": \"VALUE1\"\n"
        "    },\n"
        "    \"requirements\": [\n"
        "        \"foo\"\n"
        "    ]\n"
        "}"
    )

    assert len(environment) == len(data)
    assert sorted(environment) == sorted(data)


def test_minimal_package_without_variant():
    """Create minimal package instance created with no variant."""
    definition = wiz.definition.Definition({"identifier": "test"})

    package = wiz.package.create(definition)
    assert package.identifier == "test"
    assert package.qualified_identifier == "test"
    assert package.definition == definition
    assert package.version == "-"
    assert package.variant_name is None
    assert package.description == "-"
    assert package.command == {}
    assert package.environ == {}
    assert package.requirements == []

    assert len(package) == 2
    assert sorted(package) == ["definition", "identifier"]


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

    package = wiz.package.create(definition)
    assert package.identifier == "test==0.3.4"
    assert package.qualified_identifier == "test==0.3.4"
    assert package.definition == definition
    assert package.version == Version("0.3.4")
    assert package.variant_name is None
    assert package.description == "Test definition"
    assert package.command == {"app1": "App1", "app2": "App2"}
    assert package.environ == {"KEY1": "VALUE1", "KEY2": "VALUE2"}
    assert package.requirements == definition.requirements


def test_package_with_variant(mocked_combine_environ, mocked_combine_command):
    """Create full package instance created with variant."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "command": {
            "app": "App",
        },
        "environ": {
            "key": "value",
        },
        "requirements": [
            "test1 >= 2",
            "test2"
        ],
        "variants": [
            {
                "identifier": "Variant1",
                "install-location": "/tmp",
                "environ": {
                    "key1": "value1",
                },
                "command": {
                    "app1": "App1",
                },
                "requirements": [
                    "test3 >= 1.0, < 2"
                ]
            }
        ]
    })

    package = wiz.package.create(
        definition, variant_identifier="Variant1"
    )
    assert package.identifier == "test[Variant1]==0.1.0"
    assert package.get("install-location") == "/tmp"
    assert package.qualified_identifier == "test[Variant1]==0.1.0"
    assert package.definition == definition
    assert package.version == Version("0.1.0")
    assert package.variant_name == "Variant1"
    assert package.description == "This is a definition"
    assert package.command == {"APP": "APP_EXE"}
    assert package.environ == {"KEY": "VALUE"}
    assert package.requirements == [
        Requirement("test1 >= 2"),
        Requirement("test2"),
        Requirement("test3 >= 1.0, < 2")
    ]

    mocked_combine_environ.assert_called_once_with(
        "test[Variant1]==0.1.0",
        {"key": "value"},
        {"key1": "value1"}
    )

    mocked_combine_command.assert_called_once_with(
        "test[Variant1]==0.1.0",
        {"app": "App"},
        {"app1": "App1"}
    )


def test_package_with_namespace():
    """Create package instance with namespaces."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "Foo",
    })

    package = wiz.package.create(definition)

    assert package.identifier == "test==0.1.0"
    assert package.qualified_identifier == "Foo::test==0.1.0"
    assert package.definition == definition
    assert package.version == Version("0.1.0")


def test_package_localized_environ():
    """Return localized environment."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "install-location": "/path/to/package",
        "environ": {
            "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
            "PYTHONPATH": (
                "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
            )
        }
    })

    package = wiz.package.Package(definition)

    assert package.localized_environ() == {
        "PATH": "/path/to/package/bin:${PATH}",
        "PYTHONPATH": (
            "/path/to/package/lib/python2.7/site-packages:${PYTHONPATH}"
        )
    }


def test_package_localized_environ_with_root():
    """Return localized environment."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "install-root": "/path/to/root",
        "install-location": "${INSTALL_ROOT}/data",
        "environ": {
            "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
            "PYTHONPATH": (
                "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
            )
        }
    })

    package = wiz.package.Package(definition)

    assert package.localized_environ() == {
        "PATH": "/path/to/root/data/bin:${PATH}",
        "PYTHONPATH": (
            "/path/to/root/data/lib/python2.7/site-packages:${PYTHONPATH}"
        )
    }


def test_package_localized_environ_without_key():
    """Return localized environment with 'install-location' key."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "environ": {
            "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
            "PYTHONPATH": (
                "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
            )
        }
    })

    package = wiz.package.Package(definition)

    assert package.localized_environ() == {
        "PATH": "${INSTALL_LOCATION}/bin:${PATH}",
        "PYTHONPATH": (
            "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
        )
    }


def test_package_set():
    """Create new package from existing package with new element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package2 = package1.set("description", "This is a test")
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "description": "This is a test",
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }


def test_package_update():
    """Create new package from existing package with updated element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package2 = package1.update(
        "environ", {"key1": "value1", "key2": "value2"}
    )
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package3 = package2.update(
        "environ", {"key1": "VALUE1", "key3": "value3"}
    )
    assert package3.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "VALUE1",
            "key2": "value2",
            "key3": "value3"
        }
    }
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }


def test_package_update_error():
    """Fail to create new package with non-dictionary element updated."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    with pytest.raises(ValueError):
        package1.update("identifier", {"key1": "value1"})


def test_package_extend():
    """Create new package from existing package with extended element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package2 = package1.extend(
        "requirements", [Requirement("bar"), Requirement("bim>=1")]
    )
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [Requirement("bar"), Requirement("bim>=1")]
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package3 = package2.extend(
        "requirements", [Requirement("test")]
    )
    assert package3.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("bar"), Requirement("bim>=1"), Requirement("test")
        ]
    }
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [Requirement("bar"), Requirement("bim>=1")]
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }


def test_package_extend_error():
    """Fail to create new package with non-list element extended."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    with pytest.raises(ValueError):
        package1.extend("identifier", ["test"])


def test_package_insert():
    """Create new package from existing package with extended element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package2 = package1.set(
        "requirements", [Requirement("bar"), Requirement("bim>=1")]
    )
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [Requirement("bar"), Requirement("bim>=1")]
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    package3 = package2.insert(
        "requirements", Requirement("test"), 0
    )
    assert package3.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"), Requirement("bar"), Requirement("bim>=1")
        ]
    }
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [Requirement("bar"), Requirement("bim>=1")]
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }


def test_package_insert_error():
    """Fail to create new package with non-list element extended."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    with pytest.raises(ValueError):
        package1.insert("identifier", ["test"], 0)


def test_package_remove():
    """Create new package from existing package without element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "description": "This is a test"
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "description": "This is a test"
    }

    package2 = package1.remove("description")
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "description": "This is a test"
    }


def test_package_remove_non_existing():
    """Do not raise when removing non existing element."""
    package = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    })

    assert package.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }

    _package = package.remove("error")
    assert _package == package


def test_package_remove_key():
    """Create new package from existing package without element key."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    package2 = package1.remove_key("environ", "key1")
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key2": "value2"
        }
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }


def test_package_remove_last_key():
    """Create new package from existing package without element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    package2 = package1.remove_key("environ", "key1")
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }


def test_package_remove_key_error():
    """Fail to create new package without un-existing element or element key.
    """
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    with pytest.raises(ValueError) as error:
        package1.remove_key("identifier", "key42")

    assert (
       "Impossible to remove key from 'identifier' as it is not a dictionary."
    ) in str(error)


def test_package_remove_non_existing_key():
    """Do not raise when removing non existing element key."""
    package = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    })

    assert package.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    _package = package.remove_key("test", "error")
    assert package == _package

    _package = package.remove_key("environ", "key42")
    assert package == _package


def test_package_remove_index():
    """Create new package from existing package without element index."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }

    package2 = package1.remove_index("requirements", 0)
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }

    package3 = package2.remove_index("requirements", 1)
    assert package3.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("bar"),
        ]
    }
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }


def test_package_remove_last_index():
    """Create new package from existing package without element."""
    package1 = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
    })

    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
    }

    package2 = package1.remove_index("requirements", 0)
    assert package2.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
    }
    assert package1.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
    }


def test_package_remove_index_error():
    """Fail to create package without un-existing element or element index.
    """
    package = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    })

    assert package.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }

    with pytest.raises(ValueError) as error:
        package.remove_index("identifier", 42)

    assert (
       "Impossible to remove index from 'identifier' as it is not a list."
    ) in str(error)


def test_package_remove_non_existing_index():
    """Do not raise when removing non existing element index."""
    package = wiz.package.Package({
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
    })

    assert package.to_dict() == {
        "identifier": "foo==0.1.0",
        "version": Version("0.1.0"),
        "definition-identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
    }

    _package = package.remove_index("requirements", 5)
    assert package == _package

    _package = package.remove_index("test", "error")
    assert package == _package


def test_package_non_mutated_input():
    """Ensure that input mapping isn't mutated when creating package."""
    data = {
        "identifier": "test[V1]==0.1.0",
        "version": "0.1.0",
        "definition-identifier": "test",
        "variant-name": "V1",
        "description": "This is a definition",
        "registry": "/path/to/registry",
        "definition-location": "/path/to/registry/test-0.1.0.json",
        "auto-use": True,
        "system": {
            "platform": "linux",
            "os": "el >= 6, < 7",
            "arch": "x86_64"
        },
        "command": {
            "app": "AppX"
        },
        "environ": {
            "KEY1": "VALUE1"
        },
        "requirements": ["foo"]
    }

    _data = copy.deepcopy(data)
    wiz.package.Package(_data)

    assert data == _data

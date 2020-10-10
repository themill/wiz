# :coding: utf-8

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
def mocked_package_constructor(mocker):
    """Return mocked Package constructor."""
    return mocker.patch.object(wiz.package, "Package")


@pytest.fixture()
def mocked_package_create(mocker):
    """Return mocked :func:`wiz.package.create`."""
    return mocker.patch.object(wiz.package, "create")


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
def mocked_environ_sanitize(mocker):
    """Return mocked 'wiz.environ.sanitize' function."""
    return mocker.patch.object(
        wiz.environ, "sanitize", return_value={"CLEAN_KEY": "CLEAN_VALUE"}
    )


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_without_variant(
    mocked_definition_query, mocked_package_create, kwargs, namespace_counter
):
    """Extract one Package from definition."""
    definition = wiz.definition.Definition({"identifier": "test",})
    mocked_definition_query.return_value = definition

    requirement = Requirement("test")
    packages = wiz.package.extract(
        requirement, "__DEFINITION_MAPPING__", **kwargs
    )

    mocked_definition_query.assert_called_once_with(
        requirement, "__DEFINITION_MAPPING__",
        namespace_counter=namespace_counter
    )

    mocked_package_create.assert_called_once_with(definition)
    assert packages == [mocked_package_create.return_value]


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_with_all_variants(
    mocked_definition_query, mocked_package_create, kwargs, namespace_counter
):
    """Extract all variant Packages from definition."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "variants": [
            {"identifier": "V3"},
            {"identifier": "V2"},
            {"identifier": "V1"},
        ]
    })
    mocked_definition_query.return_value = definition

    requirement = Requirement("test")
    packages = wiz.package.extract(
        requirement, "__DEFINITION_MAPPING__", **kwargs
    )

    mocked_definition_query.assert_called_once_with(
        requirement, "__DEFINITION_MAPPING__",
        namespace_counter=namespace_counter
    )

    assert mocked_package_create.call_count == 3
    mocked_package_create.assert_any_call(definition, variant_identifier="V3")
    mocked_package_create.assert_any_call(definition, variant_identifier="V2")
    mocked_package_create.assert_any_call(definition, variant_identifier="V1")

    assert packages == [
        mocked_package_create.return_value,
        mocked_package_create.return_value,
        mocked_package_create.return_value,
    ]


@pytest.mark.parametrize("kwargs, namespace_counter", [
    ({}, None),
    ({"namespace_counter": "COUNTER"}, "COUNTER")
], ids=[
    "simple",
    "with-namespace-hints",
])
def test_extract_with_one_requested_variant(
    mocked_definition_query, mocked_package_create, kwargs, namespace_counter
):
    """Extract one requested variant Package from definition."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "variants": [
            {"identifier": "V3"},
            {"identifier": "V2"},
            {"identifier": "V1"},
        ]
    })
    mocked_definition_query.return_value = definition

    requirement = Requirement("test[V2]")
    packages = wiz.package.extract(
        requirement, "__DEFINITION_MAPPING__", **kwargs
    )

    mocked_definition_query.assert_called_once_with(
        requirement, "__DEFINITION_MAPPING__",
        namespace_counter=namespace_counter
    )

    mocked_package_create.assert_called_once_with(
        definition, variant_identifier="V2"
    )
    assert packages == [mocked_package_create.return_value]


def test_extract_context_without_packages(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitize
):
    """Extract context with no packages."""
    assert wiz.package.extract_context([]) == {
        "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_not_called()
    mocked_combine_command.assert_not_called()
    mocked_environ_sanitize.assert_called_once_with({})


def test_extract_context_with_empty_package(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitize
):
    """Extract context with package without environ nor command."""
    definition = wiz.definition.Definition({"identifier": "test"})
    packages = [wiz.package.Package(definition)]

    assert wiz.package.extract_context(packages) == {
        "command": {"APP": "APP_EXE"}, "environ": {"CLEAN_KEY": "CLEAN_VALUE"}
    }
    mocked_combine_environ.assert_called_once_with("test", {}, {})
    mocked_combine_command.assert_called_once_with("test", {}, {})
    mocked_environ_sanitize.assert_called_once_with({"KEY": "VALUE"})


def test_extract_context_with_one_package(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitize
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
    mocked_environ_sanitize.assert_called_once_with({"KEY": "VALUE"})


def test_extract_context_with_six_package(
    mocked_combine_environ, mocked_combine_command, mocked_environ_sanitize
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

    mocked_environ_sanitize.assert_called_once_with({"KEY": "VALUE"})


@pytest.mark.usefixtures("mocked_combine_command")
@pytest.mark.usefixtures("mocked_environ_sanitize")
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


def test_create_package(mocked_package_constructor):
    """Create package."""
    definition = wiz.definition.Definition({"identifier": "test"})

    package = wiz.package.create(definition)
    assert package == mocked_package_constructor.return_value
    mocked_package_constructor.assert_called_once_with(definition)


def test_create_package_with_variant(mocked_package_constructor):
    """Create package with variant."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "variants": [
            {"identifier": "V2"},
            {"identifier": "V1"}
        ]
    })

    package = wiz.package.create(definition, variant_identifier="V1")
    assert package == mocked_package_constructor.return_value
    mocked_package_constructor.assert_called_once_with(
        definition, variant_index=1
    )


def test_create_package_with_variant_error():
    """Fail to create package with variant."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "foo",
        "variants": [
            {"identifier": "V2"},
            {"identifier": "V1"}
        ]
    })

    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.package.create(definition, variant_identifier="invalid")

    assert (
        "The variant 'invalid' could not been resolved for 'foo::test==0.1.0'"
    ) in str(error)


def test_incorrect_package():
    """Fail to create a package."""
    # Requesting non exiting variant
    definition = wiz.definition.Definition({"identifier": "test"})

    with pytest.raises(wiz.exception.PackageError) as error:
        wiz.package.Package(definition, variant_index=3)

    assert (
        "Package cannot be created from definition 'test' with variant "
        "index #3."
    ) in str(error)

    # Failing to request variant
    definition = wiz.definition.Definition({
        "identifier": "test",
        "variants": [{"identifier": "V1"}]
    })

    with pytest.raises(wiz.exception.PackageError) as error:
        wiz.package.Package(definition)

    assert (
        "Package cannot be created from definition 'test' as no variant "
        "index is defined."
    ) in str(error)


def test_minimal_package():
    """Create a minimal package."""
    definition = wiz.definition.Definition({"identifier": "test"})

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {"identifier": "test"}
    assert package.localized_environ() == {}


def test_minimal_variant_package():
    """Create a minimal variant package."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "variants": [{"identifier": "V1"}]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_minimal_package_with_namespace():
    """Create a minimal package with namespace."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "namespace": "foo",
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "foo::test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace == "foo"
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "foo::test",
        "namespace": "foo",
    }
    assert package.localized_environ() == {}


def test_minimal_variant_package_with_namespace():
    """Create a minimal variant package with namespace."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "namespace": "foo",
        "variants": [{"identifier": "V1"}]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "foo::test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace == "foo"
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "foo::test[V1]",
        "namespace": "foo",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_version():
    """Create a package with version."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test==0.1.0"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version == Version("0.1.0")
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test==0.1.0",
        "version": "0.1.0",
    }
    assert package.localized_environ() == {}


def test_variant_package_with_version():
    """Create a variant package with version."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "variants": [{"identifier": "V1"}]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]==0.1.0"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version == Version("0.1.0")
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]==0.1.0",
        "version": "0.1.0",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_version_and_namespace():
    """Create a package with version and namespace."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "namespace": "foo",
        "version": "0.1.0",
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "foo::test==0.1.0"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version == Version("0.1.0")
    assert package.description is None
    assert package.namespace == "foo"
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "foo::test==0.1.0",
        "namespace": "foo",
        "version": "0.1.0",
    }
    assert package.localized_environ() == {}


def test_variant_package_with_version_and_namespace():
    """Create a variant package with version and namespace."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "foo",
        "variants": [{"identifier": "V1"}]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "foo::test[V1]==0.1.0"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version == Version("0.1.0")
    assert package.description is None
    assert package.namespace == "foo"
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "foo::test[V1]==0.1.0",
        "version": "0.1.0",
        "namespace": "foo",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_description():
    """Create a package with description."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "description": "This is a definition"
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description == "This is a definition"
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test",
        "description": "This is a definition",
    }
    assert package.localized_environ() == {}


def test_variant_package_with_description():
    """Create a variant package with description."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "description": "This is a definition",
        "variants": [{"identifier": "V1"}]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description == "This is a definition"
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "description": "This is a definition",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_install_location():
    """Create a package with installation location."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "install-location": "/path/to/install"
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location == "/path/to/install"
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test",
        "install-location": "/path/to/install"
    }
    assert package.localized_environ() == {}


def test_variant_package_with_install_location():
    """Create a variant package with installation location."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "install-location": "/path/to/install",
        "variants": [{
            "identifier": "V1"
        }]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location == "/path/to/install"
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "install-location": "/path/to/install",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_variant_package_with_install_location_overwrite():
    """Create a variant package with installation location overwritten."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "install-location": "/path/to/install",
        "variants": [{
            "identifier": "V1",
            "install-location": "/path/to/installV1",
        }]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location == "/path/to/installV1"
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "install-location": "/path/to/installV1",
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_command():
    """Create a package with command."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "command": {
            "app": "App0.1",
        }
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {"app": "App0.1"}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test",
        "command": {
            "app": "App0.1",
        }
    }
    assert package.localized_environ() == {}


def test_variant_package_with_command(mocked_combine_command):
    """Create a variant package with command."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "command": {
            "app": "App0.1",
        },
        "variants": [{
            "identifier": "V1",
            "command": {
                "appV1": "AppV10.1",
            }
        }]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == mocked_combine_command.return_value
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "command": mocked_combine_command.return_value,
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_environ():
    """Create a package with environment mapping."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "environ": {
            "KEY1": "VALUE1",
        }
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {"KEY1": "VALUE1"}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test",
        "environ": {
            "KEY1": "VALUE1",
        }
    }
    assert package.localized_environ() == {"KEY1": "VALUE1"}


def test_variant_package_with_environ(mocked_combine_environ):
    """Create a variant package with environment mapping."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "environ": {
            "KEY1": "VALUE1",
        },
        "variants": [{
            "identifier": "V1",
            "environ": {
                "KEY_V1": "VALUE_V1",
            },
        }]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == mocked_combine_environ.return_value
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "environ": mocked_combine_environ.return_value,
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == mocked_combine_environ.return_value


def test_package_with_requirements():
    """Create a package with requirements."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == [
        Requirement("envA >= 1.0.0"),
        Requirement("envB >= 3.4.2, < 4"),
        Requirement("envC")
    ]
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }
    assert package.localized_environ() == {}


def test_variant_package_with_requirements():
    """Create a variant package with requirements."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "requirements": [
            "envA >= 1.0.0",
        ],
        "variants": [{
            "identifier": "V1",
            "requirements": [
                "envC"
            ]
        }]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == [
        Requirement("envA >= 1.0.0"),
        Requirement("envC"),
    ]
    assert package.conditions == []
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "requirements": [
            "envA >= 1.0.0",
            "envC"
        ],
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}


def test_package_with_conditions():
    """Create a package with conditions."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "conditions": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    })

    package = wiz.package.Package(definition)
    assert package.definition == definition
    assert package.identifier == "test"
    assert package.variant is None
    assert package.variant_identifier is None
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == [
        Requirement("envA >= 1.0.0"),
        Requirement("envB >= 3.4.2, < 4"),
        Requirement("envC")
    ]
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test",
        "conditions": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }
    assert package.localized_environ() == {}

    package.conditions_processed = True
    assert package.conditions_processed is True


def test_variant_package_with_conditions():
    """Create a variant package with conditions."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "conditions": [
            "envA >= 1.0.0",
        ],
        "variants": [{"identifier": "V1"}]
    })

    package = wiz.package.Package(definition, variant_index=0)
    assert package.definition == definition
    assert package.identifier == "test[V1]"
    assert package.variant == definition.variants[0]
    assert package.variant_identifier == "V1"
    assert package.version is None
    assert package.description is None
    assert package.namespace is None
    assert package.install_location is None
    assert package.environ == {}
    assert package.command == {}
    assert package.requirements == []
    assert package.conditions == [
        Requirement("envA >= 1.0.0"),
    ]
    assert package.conditions_processed is False

    assert package.data() == {
        "identifier": "test[V1]",
        "conditions": [
            "envA >= 1.0.0",
        ],
        "variant-identifier": "V1"
    }
    assert package.localized_environ() == {}

    package.conditions_processed = True
    assert package.conditions_processed is True


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

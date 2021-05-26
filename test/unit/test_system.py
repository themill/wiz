# :coding: utf-8

import platform

import pytest
import distro

import wiz.definition
import wiz.exception
import wiz.system
from wiz.utility import Version


@pytest.fixture()
def mocked_platform_system(mocker):
    """Mocked the platform.system function."""
    return mocker.patch.object(platform, "system")


@pytest.fixture()
def mocked_platform_machine(mocker):
    """Mocked the platform.machine function."""
    return mocker.patch.object(platform, "machine")


@pytest.fixture()
def mocked_platform_linux(mocker):
    """Mocked the distro.linux_distribution function."""
    return mocker.patch.object(distro, "linux_distribution")


@pytest.fixture()
def mocked_platform_mac(mocker):
    """Mocked the platform.mac_ver function."""
    return mocker.patch.object(platform, "mac_ver")


@pytest.fixture()
def mocked_platform_win32(mocker):
    """Mocked the platform.win32_ver function."""
    return mocker.patch.object(platform, "win32_ver")


@pytest.fixture()
def mocked_query_linux(mocker):
    """Mocked the query_linux function."""
    return mocker.patch.object(
        wiz.system, "query_linux", return_value="LINUX_SYSTEM_MAPPING"
    )


@pytest.fixture()
def mocked_query_mac(mocker):
    """Mocked the query_mac function."""
    return mocker.patch.object(
        wiz.system, "query_mac", return_value="MAC_SYSTEM_MAPPING"
    )


@pytest.fixture()
def mocked_query_windows(mocker):
    """Mocked the query_windows function."""
    return mocker.patch.object(
        wiz.system, "query_windows", return_value="WINDOWS_SYSTEM_MAPPING"
    )


@pytest.mark.parametrize("_platform, expected", [
    ("Linux", "LINUX_SYSTEM_MAPPING"),
    ("Darwin", "MAC_SYSTEM_MAPPING"),
    ("Windows", "WINDOWS_SYSTEM_MAPPING")
], ids=[
    "linux",
    "mac",
    "windows",
])
@pytest.mark.usefixtures("mocked_query_linux")
@pytest.mark.usefixtures("mocked_query_mac")
@pytest.mark.usefixtures("mocked_query_windows")
def test_query(mocked_platform_system, _platform, expected):
    """Query system mapping."""
    mocked_platform_system.return_value = _platform
    assert wiz.system.query() == expected


def test_query_platform_error(mocked_platform_system):
    """Fails to query system mapping from unsupported platform."""
    mocked_platform_system.return_value = "incorrect"

    with pytest.raises(wiz.exception.UnsupportedPlatform):
        wiz.system.query()


def test_query_version_error(mocked_platform_system, mocked_platform_linux):
    """Fails to query system mapping from incorrect os version."""
    mocked_platform_system.return_value = "linux"
    mocked_platform_linux.side_effect = wiz.exception.VersionError("Error")

    with pytest.raises(wiz.exception.CurrentSystemError):
        wiz.system.query()


@pytest.mark.parametrize("distribution, architecture, expected", [
    (
        ("centos", "7.3.1611", "Core"), "x86_64",
        {
            "platform": "linux",
            "arch": "x86_64",
            "os": {"name": "centos", "version": Version("7.3.1611")}
        }
    ),
    (
        ("centos", "6.5", "Final"), "x86_64",
        {
            "platform": "linux",
            "arch": "x86_64",
            "os": {"name": "centos", "version": Version("6.5")}
        }
    ),
    (
        ("redhat", "5.7", "Final"), "i386",
        {
            "platform": "linux",
            "arch": "i386",
            "os": {"name": "redhat", "version": Version("5.7")}
        }
    )
], ids=[
    "centos-7-64b",
    "centos-6-64b",
    "redhat-5-32b",
])
def test_query_linux(
    mocked_platform_linux, mocked_platform_machine,
    distribution, architecture, expected
):
    """Query linux system mapping."""
    mocked_platform_linux.return_value = distribution
    mocked_platform_machine.return_value = architecture
    assert wiz.system.query_linux() == expected


@pytest.mark.parametrize("mac_ver, architecture, expected", [
    (
        ("10.13.3", ("", "", ""), ""), "x86_64",
        {
            "platform": "mac",
            "arch": "x86_64",
            "os": {"name": "mac", "version": Version("10.13.3")}
        }
    ),
    (
        ("10.11.6", ("", "", ""), ""), "x86_64",
        {
            "platform": "mac",
            "arch": "x86_64",
            "os": {"name": "mac", "version": Version("10.11.6")}
        }
    )
], ids=[
    "mac-10.13",
    "mac-10.11",
])
def test_query_mac(
    mocked_platform_mac, mocked_platform_machine,
    mac_ver, architecture, expected
):
    """Query mac system mapping."""
    mocked_platform_mac.return_value = mac_ver
    mocked_platform_machine.return_value = architecture
    assert wiz.system.query_mac() == expected


@pytest.mark.parametrize("win32_ver, architecture, expected", [
    (
        ("XP", "5.1.2600", "SP2", "Multiprocessor Free"), "i386",
        {
            "platform": "windows",
            "arch": "i386",
            "os": {"name": "windows", "version": Version("5.1.2600")}
        }
    ),
    (
        ("10", "10.0.16299", "", "Multiprocessor Free"), "AMD64",
        {
            "platform": "windows",
            "arch": "AMD64",
            "os": {"name": "windows", "version": Version("10.0.16299")}
        }
    )
], ids=[
    "windows-xp",
    "windows-10",
])
def test_query_windows(
    mocked_platform_win32, mocked_platform_machine,
    win32_ver, architecture, expected
):
    """Query mac system mapping."""
    mocked_platform_win32.return_value = win32_ver
    mocked_platform_machine.return_value = architecture
    assert wiz.system.query_windows() == expected


@pytest.mark.parametrize("definition_data, expected", [
    ({"identifier": "test"}, True),
    ({"identifier": "test", "system": {"platform": "linux"}}, True),
    ({"identifier": "test", "system": {"platform": "other"}}, False),
    ({"identifier": "test", "system": {"arch": "x86_64"}}, True),
    ({"identifier": "test", "system": {"arch": "i386"}}, False),
    ({"identifier": "test", "system": {"os": "centos"}}, True),
    ({"identifier": "test", "system": {"os": "ubuntu"}}, False),
    ({"identifier": "test", "system": {"os": "el"}}, True),
    ({"identifier": "test", "system": {"os": "centos<7"}}, False),
    ({"identifier": "test", "system": {"os": "centos>=7,<8"}}, True),
], ids=[
    "no-system",
    "filter-linux",
    "filter-other-platform",
    "filter-x86_64",
    "filter-other-arch",
    "filter-centos",
    "filter-ubuntu",
    "filter-el",
    "filter-centos-inf-7",
    "filter-centos-7-to-8",
])
def test_validate_for_centos73_64(definition_data, expected):
    """Validate definition for CentOS 7.3, architecture x86_64."""
    system_mapping = {
        "platform": "linux",
        "arch": "x86_64",
        "os": {
            "name": "centos",
            "version": Version("7.5")
        }
    }

    definition = wiz.definition.Definition(definition_data)
    assert wiz.system.validate(definition, system_mapping) == expected


@pytest.mark.parametrize("definition_data, expected", [
    ({"identifier": "test"}, True),
    ({"identifier": "test", "system": {"platform": "mac"}}, True),
    ({"identifier": "test", "system": {"platform": "other"}}, False),
    ({"identifier": "test", "system": {"arch": "x86_64"}}, True),
    ({"identifier": "test", "system": {"arch": "i386"}}, False),
    ({"identifier": "test", "system": {"os": "mac"}}, True),
    ({"identifier": "test", "system": {"os": "other"}}, False),
    ({"identifier": "test", "system": {"os": "el"}}, False),
    ({"identifier": "test", "system": {"os": "mac<10"}}, False),
    ({"identifier": "test", "system": {"os": "mac>=10,<11"}}, True),
], ids=[
    "no-system",
    "filter-mac",
    "filter-other-platform",
    "filter-x86_64",
    "filter-other-arch",
    "filter-mac-os",
    "filter-other",
    "filter-el",
    "filter-mac-inf-10",
    "filter-mac-10-to-11",
])
def test_validate_for_mac_64(definition_data, expected):
    """Validate definition for MacOS 10.13.3, architecture x86_64."""
    system_mapping = {
        "platform": "mac",
        "arch": "x86_64",
        "os": {
            "name": "mac",
            "version": Version("10.13.3")
        }
    }

    definition = wiz.definition.Definition(definition_data)
    assert wiz.system.validate(definition, system_mapping) == expected


@pytest.mark.parametrize("definition_data, expected", [
    ({"identifier": "test"}, True),
    ({"identifier": "test", "system": {"platform": "windows"}}, True),
    ({"identifier": "test", "system": {"platform": "other"}}, False),
    ({"identifier": "test", "system": {"arch": "AMD64"}}, True),
    ({"identifier": "test", "system": {"arch": "i386"}}, False),
    ({"identifier": "test", "system": {"os": "windows"}}, True),
    ({"identifier": "test", "system": {"os": "other"}}, False),
    ({"identifier": "test", "system": {"os": "el"}}, False),
    ({"identifier": "test", "system": {"os": "windows<10"}}, False),
    ({"identifier": "test", "system": {"os": "windows>=10,<11"}}, True),
], ids=[
    "no-system",
    "filter-windows",
    "filter-other-platform",
    "filter-AMD64",
    "filter-other-arch",
    "filter-windows",
    "filter-other",
    "filter-el",
    "filter-mac-inf-10",
    "filter-mac-10-to-11",
])
def test_validate_for_windows_amd64(definition_data, expected):
    """Validate definition for Windows 10.0.16299, architecture AMD64."""
    system_mapping = {
        "platform": "windows",
        "arch": "AMD64",
        "os": {
            "name": "windows",
            "version": Version("10.0.16299")
        }
    }

    definition = wiz.definition.Definition(definition_data)
    assert wiz.system.validate(definition, system_mapping) == expected


def test_validate_requirement_error():
    """Fails to validate definition when os requirement is incorrect."""
    definition = wiz.definition.Definition({
        "identifier": "test",
        "system": {"os": "!!!"}
    })

    with pytest.raises(wiz.exception.DefinitionError):
        wiz.system.validate(definition, {})

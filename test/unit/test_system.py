# :coding: utf-8

import platform

import pytest
from packaging.version import Version

import wiz.system


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
    """Mocked the platform.linux_distribution function."""
    return mocker.patch.object(platform, "linux_distribution")


@pytest.fixture()
def mocked_platform_mac(mocker):
    """Mocked the platform.mac_ver function."""
    return mocker.patch.object(platform, "mac_ver")


@pytest.fixture()
def mocked_platform_win32(mocker):
    """Mocked the platform.win32_ver function."""
    return mocker.patch.object(platform, "win32_ver")


@pytest.fixture()
def mock_query_linux(mocker):
    """Mock the query_linux function."""
    mocker.patch.object(
        wiz.system, "query_linux", return_value="LINUX_SYSTEM_MAPPING"
    )


@pytest.fixture()
def mock_query_mac(mocker):
    """Mock the query_mac function."""
    mocker.patch.object(
        wiz.system, "query_mac", return_value="MAC_SYSTEM_MAPPING"
    )


@pytest.fixture()
def mock_query_windows(mocker):
    """Mock the query_windows function."""
    mocker.patch.object(
        wiz.system, "query_windows", return_value="WINDOWS_SYSTEM_MAPPING"
    )


@pytest.mark.parametrize("platform, expected", [
    ("Linux", "LINUX_SYSTEM_MAPPING"),
    ("Darwin", "MAC_SYSTEM_MAPPING"),
    ("Windows", "WINDOWS_SYSTEM_MAPPING")
], ids=[
    "linux",
    "mac",
    "windows",
])
@pytest.mark.usefixtures("mock_query_linux")
@pytest.mark.usefixtures("mock_query_mac")
@pytest.mark.usefixtures("mock_query_windows")
def test_query(mocked_platform_system, platform, expected):
    """Query system mapping."""
    mocked_platform_system.return_value = platform
    assert wiz.system.query() == expected


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
        ("10", "10.0.16299", "", "Multiprocessor Free"), "x86_64",
        {
            "platform": "windows",
            "arch": "x86_64",
            "os": {"name": "windows", "version": Version("10.0.16299")}
        }
    ),
    (

    )
], ids=[
    "windows-xp",
    "windows-10",
    "windows-nt",
])
def test_query_windows(
    mocked_platform_win32, mocked_platform_machine,
    win32_ver, architecture, expected
):
    """Query mac system mapping."""
    mocked_platform_win32.return_value = win32_ver
    mocked_platform_machine.return_value = architecture
    assert wiz.system.query_windows() == expected

# :coding: utf-8

import pytest
import subprocess

import wiz.spawn
import wiz.environ


@pytest.fixture()
def mocked_subprocess_call(mocker):
    """Return mocked subprocess.call function."""
    return mocker.patch.object(subprocess, "call")


@pytest.fixture()
def spied_environ_substitute(mocker):
    """Return mocked environ.substitute function."""
    return mocker.spy(wiz.environ, "substitute")


def test_execute(mocked_subprocess_call, spied_environ_substitute, logger):
    """Execute command within environment."""
    wiz.spawn.execute(["app_exe", "-v", "/script"], "__ENVIRON__")

    assert spied_environ_substitute.call_count == 3
    spied_environ_substitute.assert_any_call("app_exe", "__ENVIRON__")
    spied_environ_substitute.assert_any_call("-v", "__ENVIRON__")
    spied_environ_substitute.assert_any_call("/script", "__ENVIRON__")

    mocked_subprocess_call.assert_called_once_with(
        ["app_exe", "-v", "/script"], env="__ENVIRON__"
    )

    logger.info.assert_called_once_with("Start command: app_exe -v /script")
    logger.error.assert_not_called()
    logger.debug.assert_not_called()


def test_execute_fail(mocked_subprocess_call, spied_environ_substitute, logger):
    """Fail to execute command within environment."""
    exception = OSError("Oh Shit!")
    mocked_subprocess_call.side_effect = exception

    wiz.spawn.execute(["app_exe", "-v", "/script"], "__ENVIRON__")

    assert spied_environ_substitute.call_count == 3
    spied_environ_substitute.assert_any_call("app_exe", "__ENVIRON__")
    spied_environ_substitute.assert_any_call("-v", "__ENVIRON__")
    spied_environ_substitute.assert_any_call("/script", "__ENVIRON__")

    mocked_subprocess_call.assert_called_once_with(
        ["app_exe", "-v", "/script"], env="__ENVIRON__"
    )

    logger.info.assert_called_once_with("Start command: app_exe -v /script")
    logger.error.assert_called_once_with(
        "Executable can not be found within resolved environment [app_exe]"
    )

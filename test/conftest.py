# :coding: utf-8

import os
import shutil
import tempfile
import uuid

import pytest


@pytest.fixture()
def unique_name():
    """Return a unique name."""
    return "unique-{0}".format(uuid.uuid4())


@pytest.fixture()
def temporary_file(request):
    """Return a temporary file path."""
    file_handle, path = tempfile.mkstemp()
    os.close(file_handle)

    def cleanup():
        """Remove temporary file."""
        try:
            os.remove(path)
        except OSError:
            pass

    request.addfinalizer(cleanup)
    return path


@pytest.fixture()
def temporary_directory(request):
    """Return a temporary directory path."""
    path = tempfile.mkdtemp()

    def cleanup():
        """Remove temporary directory."""
        shutil.rmtree(path)

    request.addfinalizer(cleanup)

    return path


@pytest.fixture(autouse=True)
def logger(mocker):
    """Mock the 'wiz.logging' module and return logger."""
    import wiz.logging
    mocker.patch.object(wiz.logging, "configure")
    mocker.patch.object(wiz.logging, "root")

    mock_logger = mocker.Mock()
    mocker.patch.object(
        wiz.logging, "Logger", return_value=mock_logger
    )
    return mock_logger

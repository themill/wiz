# :coding: utf-8

import io
import gzip

import pytest

import wiz.filesystem


@pytest.fixture()
def mocked_ensure_directory(mocker):
    """Return mocked ensure_directory function."""
    return mocker.patch.object(wiz.filesystem, "ensure_directory")


@pytest.fixture()
def mocked_io_open(mocker):
    """Return mocked io.open function."""
    mocked_function = mocker.patch.object(io, "open")
    stream = mocker.MagicMock()
    mocked_function.return_value.__enter__.return_value = stream
    return {
        "func": mocked_function,
        "stream": stream
    }


@pytest.fixture()
def mocked_gzip_open(mocker):
    """Return mocked gzip.open function."""
    mocked_function = mocker.patch.object(gzip, "open")
    stream = mocker.MagicMock()
    mocked_function.return_value.__enter__.return_value = stream
    return {
        "func": mocked_function,
        "stream": stream
    }


@pytest.mark.parametrize("path, resolved_path, directory", [
    ("/path/to/file", "/path/to/file", "/path/to"),
    ("/path/to/somewhere/../else/file", "/path/to/else/file", "/path/to/else"),
    ("~/file", "/usr/people/me/file", "/usr/people/me"),
], ids=[
    "simple",
    "relative",
    "with-user-shortcut"
])
def test_export(
    path, resolved_path, directory, mocked_io_open, mocked_gzip_open,
    mocked_ensure_directory, monkeypatch
):
    """Export a file with content."""
    monkeypatch.setenv("HOME", "/usr/people/me")

    content = "THIS IS\n A TEST.\n"

    wiz.filesystem.export(path, content)

    mocked_ensure_directory.assert_called_once_with(directory)
    mocked_io_open["func"].assert_called_once_with(
        resolved_path, "w", encoding="utf8"
    )
    mocked_gzip_open["func"].assert_not_called()
    mocked_io_open["stream"].write.assert_called_once_with(content)


def test_export_with_compression(
    mocked_io_open, mocked_gzip_open, mocked_ensure_directory
):
    """Export a compressed file with content."""
    content = "THIS IS\n A TEST.\n"
    path = "/path/to/output"

    wiz.filesystem.export(path, content, compressed=True)

    mocked_ensure_directory.assert_called_once_with("/path/to")
    mocked_gzip_open["func"].assert_called_once_with(path, "wb")
    mocked_io_open["func"].assert_not_called()
    mocked_gzip_open["stream"].write.assert_called_once_with(content)


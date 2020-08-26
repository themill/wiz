# :coding: utf-8

import os
import io
import gzip

import pytest

import wiz.filesystem


@pytest.fixture()
def mocked_ensure_directory(mocker):
    """Return mocked ensure_directory function."""
    return mocker.patch.object(wiz.filesystem, "ensure_directory")


@pytest.fixture()
def mocked_os_access(mocker):
    """Return mocked os.access function."""
    return mocker.patch.object(os, "access")


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


@pytest.mark.parametrize("path, resolved_path, directory", [
    ("/path/to/file", "/path/to/file", "/path/to"),
    ("/path/to/somewhere/../else/file", "/path/to/else/file", "/path/to/else"),
    ("~/file", "/usr/people/me/file", "/usr/people/me"),
], ids=[
    "simple",
    "relative",
    "with-user-shortcut"
])
def test_export_with_compression(
    path, resolved_path, directory, mocked_io_open, mocked_gzip_open,
    mocked_ensure_directory, monkeypatch
):
    """Export a compressed file with content."""
    monkeypatch.setenv("HOME", "/usr/people/me")

    content = "THIS IS\n A TEST.\n"

    wiz.filesystem.export(path, content, compressed=True)

    mocked_ensure_directory.assert_called_once_with(directory)
    mocked_gzip_open["func"].assert_called_once_with(resolved_path, "wb")
    mocked_io_open["func"].assert_not_called()
    mocked_gzip_open["stream"].write.assert_called_once_with(content)


def test_accessible(temporary_directory, temporary_file, mocked_os_access):
    """Indicate whether directory is accessible."""
    mocked_os_access.return_value = True
    assert wiz.filesystem.is_accessible(temporary_directory) is True
    assert wiz.filesystem.is_accessible(temporary_file) is False
    assert wiz.filesystem.is_accessible("/incorrect") is False

    mocked_os_access.return_value = False
    assert wiz.filesystem.is_accessible(temporary_directory) is False


def test_ensure_directory(temporary_directory, temporary_file):
    """Create directory if it doesn't exist."""
    path1 = os.path.join(temporary_directory, "path1")
    path2 = os.path.join(path1, "path2")
    assert os.path.isdir(path1) is False
    assert os.path.isdir(path2) is False

    wiz.filesystem.ensure_directory(path2)
    assert os.path.isdir(path1) is True
    assert os.path.isdir(path2) is True

    # Do not raise when folder exists
    wiz.filesystem.ensure_directory(path2)

    # Raise when element is a file
    with pytest.raises(OSError):
        wiz.filesystem.ensure_directory(temporary_file)

    # Raise for other errors
    with pytest.raises(OSError):
        wiz.filesystem.ensure_directory("/incorrect")


def test_sanitize_value():
    """Sanitize value."""
    value = "/path/to/a-file/with: A F@#%ing Name!!!"
    assert wiz.filesystem.sanitize_value(value) == (
        "/path/to/a-file/with:_A_F__%ing_Name___"
    )

    assert wiz.filesystem.sanitize_value(value, substitution_character="-") == (
        "/path/to/a-file/with:-A-F--%ing-Name---"
    )

    assert wiz.filesystem.sanitize_value(value, case_sensitive=False) == (
        "/path/to/a-file/with:_a_f__%ing_name___"
    )

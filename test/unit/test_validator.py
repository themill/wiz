# :coding: utf-8

import wiz.validator


def test_minimal_definition():
    """Validate """
    data = {"identifier": "test"}
    wiz.validator.DefinitionValidator.check_schema(data)


def test_definition_with_version():
    """Validate """
    data = {
        "identifier": "test",
        "version": "0.1.0",
    }
    wiz.validator.DefinitionValidator.check_schema(data)


def test_definition_with_description():
    data = {
        "identifier": "test",
        "description": "This is a definition"
    }
    wiz.validator.DefinitionValidator.check_schema(data)


def test_definition_with_environ():
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        }
    }
    wiz.validator.DefinitionValidator.check_schema(data)


def test_definition_with_requirements():
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }
    wiz.validator.DefinitionValidator.check_schema(data)

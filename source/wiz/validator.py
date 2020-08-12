# :coding: utf-8

import collections
import os

import ujson as json
import jsonschema.validators
from packaging.requirements import Requirement
from packaging.version import Version

#: Path to the definition :term:`JSON Schema` file.
_DEFINITION_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "package_data", "schema", "definition.json"
)

#: Loaded definition schema mapping.
_DEFINITION_SCHEMA = json.load(open(_DEFINITION_SCHEMA_PATH))

#: Create validator based on draft 4
#: (https://json-schema.org/specification-links.html#draft-4)
_VALIDATOR = jsonschema.validators.create(
    meta_schema=jsonschema.validators.Draft4Validator.META_SCHEMA,
    validators=jsonschema.validators.Draft4Validator.VALIDATORS,
    default_types=dict(
        jsonschema.validators.Draft4Validator.DEFAULT_TYPES,
        **{
            "object": collections.Mapping,
            "requirement": Requirement,
            "version": Version,
        }
    )
)


def yield_definition_errors(data):
    """Yield list of errors found in package definition data.

    An empty list is yielded if no errors are found.

    The following :term:`JSON Schema` will be used:

    .. literalinclude:: ../../source/wiz/package_data/schema/definition.json

    """
    for error in _VALIDATOR(_DEFINITION_SCHEMA).iter_errors(data):
        yield {
            "message": error.message,
            "path": "/{}".format("/".join(str(e) for e in error.path)),
            "schema_path": "/{}".format(
                "/".join(str(e) for e in error.schema_path)
            )
        }

# :coding: utf-8

import collections
import json
import os

import jsonschema.validators
from packaging.requirements import Requirement
from packaging.version import Version

#: Root directory containing the schemas.
_SCHEMA_ROOT = os.path.join(
    os.path.dirname(__file__), "package_data", "schema"
)

#: Definition schema.
_SCHEMA_DEFINITION = json.load(
    open(os.path.join(_SCHEMA_ROOT, "definition.json"))
)


# Set up custom validator base class that ensures:
#
#   * 'required' property names included in error path. From
#     https://github.com/Julian/jsonschema/issues/119#issuecomment-40461335
#   * 'collections.Mapping' is a valid 'object' type.

def _required(validator, required, instance, _):
    """Validate 'required' properties."""
    if not validator.is_type(instance, "object"):
        return

    for index, requirement in enumerate(required):
        if requirement not in instance:
            error = jsonschema.ValidationError(
                "{0!r} is a required property".format(requirement)
            )
            error.schema_path.append(index)
            yield error


_Validator = jsonschema.validators.create(
    meta_schema=jsonschema.validators.Draft4Validator.META_SCHEMA,
    version=None,
    validators=dict(
        jsonschema.validators.Draft4Validator.VALIDATORS,
        **{"required": _required}
    ),
    default_types=dict(
        jsonschema.validators.Draft4Validator.DEFAULT_TYPES,
        **{
            "object": collections.Mapping,
            "requirement": Requirement,
            "version": Version,
        }
    )
)


def _load_schema(schema_path):
    """Return schema loaded from *schema_path*."""
    with open(schema_path) as file_object:
        schema = json.load(file_object)

    return schema


def yield_definition_errors(data):
    """Yield list of errors found in package definition data.

    An empty list is yielded if no errors are found.

    The following :term:`JSON Schema` will be used:

    .. literalinclude:: ../../source/wiz/package_data/schema/definition.json

    """
    for error in _Validator(_SCHEMA_DEFINITION).iter_errors(data):
        yield {
            "message": error.message,
            "path": "/{}".format("/".join(str(e) for e in error.path)),
            "schema_path": "/{}".format(
                "/".join(str(e) for e in error.schema_path)
            )
        }

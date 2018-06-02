# :coding: utf-8

import collections
import os
import json
import urlparse

import jsonschema.validators


# Add 'wiz' scheme in "http"-like schemes in order to get the expected
# result from `urlparse.urljoin` within `RefResolver.resolve`
urlparse.uses_netloc.append("wiz")
urlparse.uses_relative.append("wiz")
urlparse.uses_fragment.append("wiz")


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
        **{"object": collections.Mapping}
    )
)


def _load_schema(schema_path):
    """Return schema loaded from *schema_path*."""
    with open(schema_path) as file_object:
        schema = json.load(file_object)

    return schema


class DefinitionValidator(_Validator):
    """Definition schema validator."""

    META_SCHEMA = _load_schema(
        os.path.join(
            os.path.dirname(__file__), "meta_schema", "definition.json"
        )
    )

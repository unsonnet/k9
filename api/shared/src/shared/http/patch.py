from typing import Any
from unittest.mock import patch

from aws_lambda_powertools.event_handler.middlewares.openapi_validation import (
    _get_body_field_location,
    _get_embed_body,
    _handle_missing_field_value,
    _normalize_field_value,
    _validate_field,
)
from aws_lambda_powertools.event_handler.openapi.compat import (
    ModelField,
    get_missing_field_error,
)

from ..config import is_set, missing


def _extract_field_value_from_body(
    field: ModelField,
    received_body: dict[str, Any] | None,
    loc: tuple[str, ...],
    errors: list[dict[str, Any]],
) -> Any | missing:
    """Extract field value from the received body, handling potential AttributeError."""
    if received_body is None:
        return missing

    try:
        return received_body.get(field.alias, missing)
    except AttributeError:
        errors.append(get_missing_field_error(loc))
        return missing


def _request_body_to_args(
    required_params: list[ModelField],
    received_body: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Convert the request body to a dictionary of values using validation, and returns a list of errors.
    """
    values: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    received_body, field_alias_omitted = _get_embed_body(
        field=required_params[0],
        required_params=required_params,
        received_body=received_body,
    )

    for field in required_params:
        loc = _get_body_field_location(field, field_alias_omitted)
        value = _extract_field_value_from_body(field, received_body, loc, errors)

        # If we don't have a value, see if it's required or has a default
        if not is_set(value):
            _handle_missing_field_value(field, values, errors, loc)
            continue

        value = _normalize_field_value(value=value, field_info=field.field_info)
        values[field.name] = _validate_field(
            field=field, value=value, loc=loc, existing_errors=errors
        )

    return values, errors


patch(
    "aws_lambda_powertools.event_handler.middlewares.openapi_validation._request_body_to_args",
    _request_body_to_args,
).start()

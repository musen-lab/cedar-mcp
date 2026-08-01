#!/usr/bin/env python3

"""Cleaning and transformation of CEDAR template instances in JSON-LD format."""

from typing import Any, Dict


def clean_template_instance_response(instance_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and transform CEDAR template instance JSON-LD to simplified structure.

    Removes metadata fields and transforms JSON-LD specific attributes:
    - Removes: '@context', 'schema:isBasedOn', 'schema:name', 'schema:description',
               'pav:createdOn', 'pav:createdBy', 'pav:derivedFrom', 'oslc:modifiedBy', '@id' from root
    - Transforms: '@id' → 'iri', 'rdfs:label' → 'label' throughout
    - Flattens: '@value' objects to their direct values

    Args:
        instance_data: Raw instance data from CEDAR (JSON-LD format)

    Returns:
        Cleaned and transformed instance data as dictionary
    """
    # Remove metadata fields from root level
    metadata_fields = {
        "@context",
        "schema:isBasedOn",
        "schema:name",
        "schema:description",
        "pav:createdOn",
        "pav:createdBy",
        "pav:derivedFrom",
        "oslc:modifiedBy",
        "@id",
    }

    # Create cleaned copy
    cleaned_data = {}
    for key, value in instance_data.items():
        if key not in metadata_fields:
            cleaned_data[key] = value

    # Recursively transform the entire structure
    return _transform_jsonld_structure(cleaned_data)


def _transform_jsonld_structure(obj: Any) -> Any:
    """
    Recursively transform JSON-LD structure to simplified format.

    This function handles:
    - @value flattening with optional type conversion based on @type
    - @context removal from nested objects
    - @id -> iri transformation (except for template-element-instances)
    - rdfs:label -> label transformation
    - Recursive processing of nested structures

    Args:
        obj: Any JSON-LD object (dict, list, or primitive)

    Returns:
        Transformed object with simplified structure
    """
    if isinstance(obj, dict):
        return _transform_dictionary(obj)
    elif isinstance(obj, list):
        # Transform each item in the list
        return [_transform_jsonld_structure(item) for item in obj]
    else:
        # Primitive types (str, int, float, bool, None) - return as-is
        return obj


def _transform_dictionary(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a dictionary object, handling special JSON-LD keys and recursion.

    Args:
        obj: Dictionary to transform

    Returns:
        Transformed dictionary
    """
    # First check if this is a @value object that should be flattened
    flattened_value = _handle_value_flattening(obj)
    if flattened_value is not None:
        return flattened_value

    # Transform dictionary
    transformed = {}
    for key, value in obj.items():
        # Skip keys that shouldn't be processed
        if _should_skip_key(key, obj):
            continue

        # Skip template-element-instance @id fields
        if _should_skip_template_element_instance_id(key, value):
            continue

        # Transform the key name
        new_key = _transform_key_name(key)

        # Recursively transform the value
        transformed[new_key] = _transform_jsonld_structure(value)

    return transformed


def _handle_value_flattening(obj: Dict[str, Any]) -> Any:
    """
    Handle @value flattening with optional type conversion.

    Args:
        obj: Dictionary that may contain @value and @type keys

    Returns:
        Flattened/converted value or None if not a @value object
    """
    if "@value" not in obj:
        return None

    value = obj["@value"]

    # If only @value is present, return the value as-is
    if len(obj) == 1:
        return value

    # If @type is present along with @value, convert based on type
    if "@type" in obj and len(obj) == 2:
        xsd_type = obj["@type"]
        return _convert_xsd_value(value, xsd_type)

    # If there are other keys besides @value and @type, don't flatten
    return None


def _convert_xsd_value(value: Any, xsd_type: str) -> Any:
    """
    Convert a value based on its XSD type.

    Args:
        value: The value to convert
        xsd_type: The XSD type string (e.g., "xsd:decimal", "xsd:integer")

    Returns:
        Converted value or original value if conversion fails
    """
    # Handle numeric types
    if xsd_type in {"xsd:decimal", "xsd:float", "xsd:double"}:
        try:
            return float(value)
        except (ValueError, TypeError):
            return value  # Return original if conversion fails

    elif xsd_type in {"xsd:int", "xsd:integer", "xsd:long", "xsd:short", "xsd:byte"}:
        try:
            return int(value)
        except (ValueError, TypeError):
            return value  # Return original if conversion fails

    elif xsd_type == "xsd:boolean":
        if isinstance(value, str):
            return value.lower() in {"true", "1"}
        else:
            return bool(value)

    else:
        # For string types (xsd:string, xsd:date, xsd:dateTime, etc.) or unknown types,
        # return as string
        return value


def _transform_key_name(key: str) -> str:
    """
    Transform JSON-LD key names to simplified format.

    Args:
        key: Original key name

    Returns:
        Transformed key name
    """
    if key == "@id":
        return "iri"
    elif key == "rdfs:label":
        return "label"
    else:
        return key


def _should_skip_key(key: str, obj: Dict[str, Any]) -> bool:
    """
    Determine if a key should be skipped during transformation.

    Args:
        key: The key to check
        obj: The object containing the key

    Returns:
        True if the key should be skipped
    """
    # Skip @context fields in nested objects
    if key == "@context":
        return True

    # Skip @type and @value if they were already processed for flattening
    if key in {"@type", "@value"} and "@value" in obj:
        return True

    return False


def _should_skip_template_element_instance_id(key: str, value: Any) -> bool:
    """
    Check if an @id field contains template-element-instances and should be skipped.

    Args:
        key: The key name
        value: The key value

    Returns:
        True if this is a template-element-instance @id that should be skipped
    """
    return (
        key == "@id"
        and isinstance(value, str)
        and "https://repo.metadatacenter.org/template-element-instances/" in value
    )

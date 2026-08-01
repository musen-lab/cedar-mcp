#!/usr/bin/env python3

"""Cleaning and transformation of CEDAR templates in YAML format."""

from typing import Any, Dict, List, Optional, Union

from ..model import (
    BranchConstraint,
    ClassConstraint,
    ClassOption,
    ControlledTermDefault,
    ElementDefinition,
    FieldDefinition,
    LiteralConstraint,
    OntologyConstraint,
    SimplifiedTemplate,
    ValueConstraint,
)

# CEDAR YAML field types that carry layout or decoration rather than data.
# The JSON-LD cleaner skips these too, since they are StaticTemplateFields.
_YAML_STATIC_FIELD_TYPES = {
    "static-page-break",
    "static-section-break",
    "static-image",
    "static-rich-text",
    "static-youtube-video",
}

_YAML_INTEGER_DATATYPES = {
    "xsd:int",
    "xsd:integer",
    "xsd:long",
    "xsd:short",
    "xsd:byte",
}


def _extract_yaml_datatype(field_data: Dict[str, Any]) -> str:
    """
    Determine the appropriate datatype for a field in CEDAR YAML.

    The YAML rendering names the widget in `type` (e.g. "numeric-field") and
    the underlying XSD type in `datatype`, so both are needed to arrive at the
    same datatypes the JSON-LD cleaner produces.

    Args:
        field_data: Field data from the CEDAR YAML rendering

    Returns:
        Datatype string (string, integer, decimal, boolean, date, datetime, time, link)
    """
    field_type = field_data.get("type", "")
    datatype = field_data.get("datatype", "")

    # Numeric fields carry their XSD type in `datatype`
    if field_type == "numeric-field":
        if datatype in _YAML_INTEGER_DATATYPES:
            return "integer"
        return "decimal"

    # Temporal fields carry their XSD type in `datatype`
    if field_type == "temporal-field":
        if datatype == "xsd:date":
            return "date"
        elif datatype == "xsd:time":
            return "time"
        return "datetime"

    # Checkboxes without controlled terms represent a boolean
    if field_type == "checkbox-field" and not field_data.get("values"):
        return "boolean"

    # Check for link/URI type
    if field_type == "link-field":
        return "link"

    # Default to string for text, controlled term, list fields, etc.
    return "string"


def _extract_yaml_permissible_value_definitions(
    field_data: Dict[str, Any],
) -> Optional[List[ValueConstraint]]:
    """
    Extract value constraints from the `values` list of a CEDAR YAML field.

    The YAML rendering collapses the JSON-LD `_valueConstraints` buckets into a
    single `values` list, where each entry is tagged with a `type` — except
    literals, which are bare labels.

    Args:
        field_data: Field data from the CEDAR YAML rendering

    Returns:
        List of value constraints or None if the field has no controlled values
    """
    values = field_data.get("values", [])
    if not values:
        return None

    literals: List[str] = []
    acronyms: List[str] = []
    class_options: List[ClassOption] = []
    branches: List[BranchConstraint] = []

    for value in values:
        if not isinstance(value, dict):
            continue

        value_type = value.get("type")

        # Literals are rendered as a bare label, with no type tag
        if value_type is None:
            if "label" in value:
                literals.append(value["label"])
        elif value_type == "ontology":
            if "acronym" in value:
                acronyms.append(value["acronym"])
        elif value_type == "valueSet":
            # Fold value sets into ontology acronyms, as the JSON-LD cleaner does
            if "valueSetName" in value:
                acronyms.append(value["valueSetName"])
        elif value_type == "class":
            if "iri" in value:
                class_options.append(
                    ClassOption(
                        label=value.get("termLabel", value.get("label", "")),
                        term_iri=value["iri"],
                    )
                )
        elif value_type == "branch":
            if "acronym" in value and "iri" in value:
                branches.append(
                    BranchConstraint(
                        ontology_acronym=value["acronym"],
                        branch_iri=value["iri"],
                    )
                )

    result: List[ValueConstraint] = []

    if literals:
        result.append(LiteralConstraint(options=literals))
    if acronyms:
        result.append(OntologyConstraint(ontology_acronyms=acronyms))
    if class_options:
        result.append(ClassConstraint(options=class_options))
    result.extend(branches)

    return result if result else None


def _extract_yaml_default_value(
    field_data: Dict[str, Any],
) -> Optional[Union[ControlledTermDefault, str, int, float, bool]]:
    """
    Extract the default value from a CEDAR YAML field.

    Controlled term defaults are rendered as a `value`/`label` pair, everything
    else as a plain scalar. Radio and list fields instead mark the default
    option with `selected: true`.

    Args:
        field_data: Field data from the CEDAR YAML rendering

    Returns:
        Default value or None
    """
    default_value = field_data.get("default")

    # Check for structured default value (controlled terms)
    if isinstance(default_value, dict):
        if "value" in default_value and "label" in default_value:
            return ControlledTermDefault(
                label=default_value["label"], iri=default_value["value"]
            )
        return None

    # Check for simple default values
    if default_value is not None:
        return default_value

    values = field_data.get("values", [])
    if not isinstance(values, list):
        return None

    # Check for a literal option marked as selected by default
    for value in values:
        if isinstance(value, dict) and value.get("selected") and "label" in value:
            return value["label"]

    # Check for controlled term default in branches
    for value in values:
        if (
            isinstance(value, dict)
            and value.get("type") == "branch"
            and "termLabel" in value
            and "iri" in value
        ):
            # Use the first branch as default if no other default found
            return ControlledTermDefault(label=value["termLabel"], iri=value["iri"])

    return None


def _transform_yaml_field(field_data: Dict[str, Any]) -> FieldDefinition:
    """
    Transform a single field from CEDAR YAML to output structure.

    Args:
        field_data: Field data from the CEDAR YAML rendering

    Returns:
        Transformed output field
    """
    name = field_data.get("name", field_data.get("key", ""))
    description = field_data.get("description", "")
    label = field_data.get("prefLabel", name)
    configuration = field_data.get("configuration", {})

    return FieldDefinition(
        name=name,
        description=description,
        label=label,
        type=_extract_yaml_datatype(field_data),
        required=configuration.get("required", False),
        multivalued=configuration.get("multiple", False),
        pattern=field_data.get("regex"),
        default_value=_extract_yaml_default_value(field_data),
        permissible_values=_extract_yaml_permissible_value_definitions(field_data),
    )


def _transform_yaml_element(element_data: Dict[str, Any]) -> ElementDefinition:
    """
    Transform a single template element from CEDAR YAML to output structure.

    Args:
        element_data: Element data from the CEDAR YAML rendering

    Returns:
        Transformed output element
    """
    name = element_data.get("name", element_data.get("key", ""))
    description = element_data.get("description", "")
    label = element_data.get("prefLabel", name)
    configuration = element_data.get("configuration", {})

    return ElementDefinition(
        name=name,
        description=description,
        label=label,
        type="element",
        required=configuration.get("required", False),
        multivalued=configuration.get("multiple", False),
        children=_process_yaml_children(element_data),
    )


def _process_yaml_children(
    parent_data: Dict[str, Any],
) -> List[Union[FieldDefinition, ElementDefinition]]:
    """
    Process the children of a CEDAR YAML template or element.

    The YAML rendering already lists children in display order, so no separate
    UI order lookup is needed.

    Args:
        parent_data: Template or element data containing a `children` list

    Returns:
        List of child field and element definitions
    """
    children: List[Union[FieldDefinition, ElementDefinition]] = []

    for child_data in parent_data.get("children", []) or []:
        if not isinstance(child_data, dict):
            continue

        child_type = child_data.get("type", "")

        if child_type == "element":
            children.append(_transform_yaml_element(child_data))
        elif child_type and child_type not in _YAML_STATIC_FIELD_TYPES:
            children.append(_transform_yaml_field(child_data))

    return children


def clean_template_yaml_response(
    template_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Clean and transform a CEDAR template YAML rendering to simplified structure.

    Produces the same output shape as clean_template_response, so consumers do
    not care whether the template arrived as JSON-LD or YAML. Static fields
    (rich text, section breaks, images) are dropped, as they hold layout rather
    than data.

    Args:
        template_data: Template data parsed from the CEDAR YAML rendering

    Returns:
        Cleaned and transformed template data as dictionary
    """
    template_name = template_data.get("name", "") or "Unnamed Template"

    output_template = SimplifiedTemplate(
        type="template",
        name=template_name,
        children=_process_yaml_children(template_data),
    )

    # Convert to dictionary for YAML export
    return output_template.model_dump(exclude_none=True)

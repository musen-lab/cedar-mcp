#!/usr/bin/env python3

"""Cleaning and transformation of CEDAR templates.

Templates arrive as CEDAR's YAML rendering, parsed into a dictionary.
"""

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
from .branch_expansion import normalize_expanded_branches

# CEDAR YAML field types that carry layout or decoration rather than data.
# The JSON-LD cleaner skips these too, since they are StaticTemplateFields.
_STATIC_FIELD_TYPES = {
    "static-page-break",
    "static-section-break",
    "static-image",
    "static-rich-text",
    "static-youtube-video",
}

_INTEGER_DATATYPES = {
    "xsd:int",
    "xsd:integer",
    "xsd:long",
    "xsd:short",
    "xsd:byte",
}

# Field types whose widget already implies more than one value, so CEDAR leaves
# `multiple` out of their configuration. Checkboxes are handled separately: a
# group of them is a multi-select, but a lone one is a single boolean.
_IMPLICITLY_MULTIVALUED_TYPES = {
    "attribute-value-field",
    "multi-select-list-field",
}


def _extract_datatype(field_data: Dict[str, Any]) -> str:
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
        if datatype in _INTEGER_DATATYPES:
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


def _extract_permissible_value_definitions(
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
                        # Carried over when the template was expanded first
                        options=value.get("options"),
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


def _extract_default_value(
    field_data: Dict[str, Any],
) -> Optional[Union[ControlledTermDefault, str, int, float, bool]]:
    """
    Extract the default value from a CEDAR YAML field.

    Only the `default` key counts. Controlled term defaults are rendered there
    as a `value`/`label` pair, everything else as a plain scalar.

    Two things in `values` are deliberately not treated as defaults:
    an option marked `selected: true`, which is a UI preselection rather than
    a declared default, and a branch entry, which names the subtree to pick a
    term from and so is a category rather than a value the field can hold.

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

    return None


def _is_multivalued(field_data: Dict[str, Any], configuration: Dict[str, Any]) -> bool:
    """
    Determine whether a field accepts more than one value.

    Usually this is `configuration.multiple`, but CEDAR omits that key for field
    types whose widget already implies several values: attribute-value fields,
    multi-select lists, and checkboxes. Reading the configuration alone would
    report those as single valued.

    A checkbox is the awkward one. A group of checkboxes is a multi-select over
    its options, but a checkbox with no options is a single boolean toggle, which
    is how _extract_datatype types it.

    Args:
        field_data: Field data from the CEDAR YAML rendering
        configuration: The field's configuration block

    Returns:
        True if the field accepts more than one value
    """
    if configuration.get("multiple", False):
        return True

    field_type = field_data.get("type", "")
    if field_type in _IMPLICITLY_MULTIVALUED_TYPES:
        return True

    return field_type == "checkbox-field" and bool(field_data.get("values"))


def _transform_field(field_data: Dict[str, Any]) -> FieldDefinition:
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
        type=_extract_datatype(field_data),
        required=configuration.get("required", False),
        multivalued=_is_multivalued(field_data, configuration),
        pattern=field_data.get("regex"),
        default_value=_extract_default_value(field_data),
        permissible_values=_extract_permissible_value_definitions(field_data),
    )


def _transform_element(element_data: Dict[str, Any]) -> ElementDefinition:
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
        children=_process_children(element_data),
    )


def _process_children(
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
            children.append(_transform_element(child_data))
        elif child_type and child_type not in _STATIC_FIELD_TYPES:
            children.append(_transform_field(child_data))

    return children


def clean_template_response(
    template_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Clean and transform a CEDAR template YAML rendering to simplified structure.

    Static fields (rich text, section breaks, images) are dropped, as they hold
    layout rather than data.

    Listing the terms allowed by an ontology branch is a separate concern, see
    expand_template_branches. This carries over any that are already listed, so
    the two can be applied in either order.

    Args:
        template_data: Template data parsed from the CEDAR YAML rendering

    Returns:
        Cleaned and transformed template data as dictionary
    """
    template_name = template_data.get("name", "") or "Unnamed Template"

    output_template = SimplifiedTemplate(
        type="template",
        name=template_name,
        children=_process_children(template_data),
    )

    # Convert to dictionary for YAML export
    cleaned = output_template.model_dump(exclude_none=True)

    # An expanded branch reports its terms instead of its root
    normalize_expanded_branches(cleaned)

    return cleaned

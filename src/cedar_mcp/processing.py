#!/usr/bin/env python3

from typing import Any, Dict, List, Optional, Union

from .model import (
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


def _extract_datatype(field_data: Dict[str, Any]) -> str:
    """
    Determine the appropriate datatype for a field based on its properties.

    Args:
        field_data: Field data from input JSON-LD

    Returns:
        Datatype string (string, integer, decimal, boolean)
    """
    properties = field_data.get("properties", {})
    value_props = properties.get("@value", {})

    # Check for numeric and boolean types
    if isinstance(value_props, dict) and "type" in value_props:
        value_type = value_props["type"]
        if value_type == "number":
            return "decimal"
        elif value_type == "integer":
            return "integer"
        elif value_type == "boolean":
            return "boolean"

    # Check if it's a list type that includes numbers
    if isinstance(value_props, dict) and "type" in value_props:
        if isinstance(value_props["type"], list):
            if "number" in value_props["type"]:
                return "decimal"
            elif "integer" in value_props["type"]:
                return "integer"
            elif "boolean" in value_props["type"]:
                return "boolean"

    # Default to string for text, controlled terms, links
    return "string"


def _extract_permissible_value_definitions(
    field_data: Dict[str, Any],
) -> Optional[List[ValueConstraint]]:
    """
    Extract value constraints from field constraint definitions.

    Returns typed constraint objects describing what kinds of values are allowed,
    without fetching any external data. Consumers can use the returned constraint
    metadata to query BioPortal or other services as needed.

    Args:
        field_data: Field data from input JSON-LD

    Returns:
        List of value constraints or None if not a controlled term field
    """
    constraints = field_data.get("_valueConstraints", {})

    # Check for different types of controlled vocabulary data
    literals = constraints.get("literals", [])
    ontologies = constraints.get("ontologies", [])
    value_sets = constraints.get("valueSets", [])
    classes = constraints.get("classes", [])
    branches = constraints.get("branches", [])

    # Check if this is a controlled term field
    has_controlled_terms = literals or ontologies or value_sets or classes or branches

    if not has_controlled_terms:
        return None

    result: List[ValueConstraint] = []

    # Handle literals
    if literals:
        options = [
            literal["label"]
            for literal in literals
            if isinstance(literal, dict) and "label" in literal
        ]
        if options:
            result.append(LiteralConstraint(options=options))

    # Handle ontologies
    if ontologies:
        acronyms = [
            o["acronym"]
            for o in ontologies
            if isinstance(o, dict) and "acronym" in o
        ]
        if acronyms:
            result.append(OntologyConstraint(ontology_acronyms=acronyms))

    # Handle valueSets — fold into OntologyConstraint by extracting acronyms
    if value_sets:
        vs_acronyms = [
            vs["name"]
            for vs in value_sets
            if isinstance(vs, dict) and "name" in vs
        ]
        if vs_acronyms:
            result.append(OntologyConstraint(ontology_acronyms=vs_acronyms))

    # Handle classes
    if classes:
        class_options = [
            ClassOption(label=c["prefLabel"], term_iri=c["@id"])
            for c in classes
            if isinstance(c, dict) and "prefLabel" in c and "@id" in c
        ]
        if class_options:
            result.append(ClassConstraint(options=class_options))

    # Handle branches
    for branch in branches:
        if (
            isinstance(branch, dict)
            and "uri" in branch
            and "acronym" in branch
        ):
            result.append(
                BranchConstraint(
                    ontology_acronym=branch["acronym"],
                    branch_iri=branch["uri"],
                )
            )

    return result if result else None


def _extract_default_value(
    field_data: Dict[str, Any],
) -> Optional[Union[ControlledTermDefault, str, int, float, bool]]:
    """
    Extract default value from field data.

    Args:
        field_data: Field data from input JSON-LD

    Returns:
        Default value or None
    """
    constraints = field_data.get("_valueConstraints", {})

    # Check for structured default value (controlled terms)
    default_value = constraints.get("defaultValue")
    if default_value and isinstance(default_value, dict):
        if "rdfs:label" in default_value and "termUri" in default_value:
            return ControlledTermDefault(
                label=default_value["rdfs:label"], iri=default_value["termUri"]
            )

    # Check for simple default values
    if default_value is not None and not isinstance(default_value, dict):
        return default_value

    # Check for controlled term default in branches
    branches = constraints.get("branches", [])
    if branches:
        # Use the first branch as default if no other default found
        for branch in branches:
            if isinstance(branch, dict) and "name" in branch and "uri" in branch:
                return ControlledTermDefault(label=branch["name"], iri=branch["uri"])

    return None


def _transform_field(
    field_name: str, field_data: Dict[str, Any]
) -> FieldDefinition:
    """
    Transform a single field from input JSON-LD to output structure.
    Handles both regular fields and arrays of fields.

    Args:
        field_name: Name of the field
        field_data: Field data from input JSON-LD

    Returns:
        Transformed output field
    """
    # Check if this is an array of fields
    is_field_array = field_data.get("type") == "array" and "items" in field_data

    if is_field_array:
        # For array fields, replace field data from the items structure
        field_data = field_data["items"]

    # Regular field processing
    name = field_data.get("schema:name", field_name)
    description = field_data.get("schema:description", "")
    label = field_data.get("skos:prefLabel", name)
    constraints = field_data.get("_valueConstraints", {})

    # Determine datatype
    type = _extract_datatype(field_data)

    # Extract controlled term values
    permissible_values = _extract_permissible_value_definitions(field_data)

    # Extract default value
    default_value = _extract_default_value(field_data)

    # Extract regex if present
    pattern = constraints.get("regex")

    # Extract configuration
    required = constraints.get("requiredValue", False)
    return FieldDefinition(
        name=name,
        description=description,
        label=label,
        type=type,
        required=required,
        multivalued=is_field_array,
        pattern=pattern,
        default_value=default_value,
        permissible_values=permissible_values,
    )


def _transform_element(
    element_name: str, element_data: Dict[str, Any]
) -> ElementDefinition:
    """
    Transform a single template element from input JSON-LD to output structure.

    Args:
        element_name: Name of the element
        element_data: Element data from input JSON-LD

    Returns:
        Transformed output element
    """
    # Check if this is an array element
    is_array = element_data.get("type") == "array"

    # For array elements, extract information from the items structure
    if is_array and "items" in element_data:
        item_data = element_data["items"]
        name = item_data.get("schema:name", element_name)
        description = item_data.get("schema:description", "")
        pref_label = item_data.get("skos:prefLabel", name)
        constraints = item_data.get("_valueConstraints", {})
        children = _process_element_children(item_data)
    else:
        # For regular elements, extract from the element itself
        name = element_data.get("schema:name", element_name)
        description = element_data.get("schema:description", "")
        pref_label = element_data.get("skos:prefLabel", name)
        constraints = element_data.get("_valueConstraints", {})
        children = _process_element_children(element_data)

    # Extract configuration
    required = constraints.get("requiredValue", False)
    # Process nested children
    children_list: List[Union[FieldDefinition, ElementDefinition]] = children

    return ElementDefinition(
        name=name,
        description=description,
        label=pref_label,
        type="element",
        required=required,
        multivalued=is_array,
        children=children_list,
    )


def _process_element_children(
    element_data: Dict[str, Any],
) -> List[Union[FieldDefinition, ElementDefinition]]:
    """
    Process the children of a template element, handling nested fields and elements.

    Args:
        element_data: Element data containing properties and UI order

    Returns:
        List of child field and element definitions
    """
    children: List[Union[FieldDefinition, ElementDefinition]] = []

    # Get field order from UI configuration
    ui_config = element_data.get("_ui", {})
    field_order = ui_config.get("order", [])

    # Get properties section
    properties = element_data.get("properties", {})

    # Process children in the specified UI order
    for child_name in field_order:
        if child_name in properties:
            child_data = properties[child_name]
            if isinstance(child_data, dict):
                child_type = child_data.get("@type", "")

                if child_type == "https://schema.metadatacenter.org/core/TemplateField":
                    # It's a field
                    field_child = _transform_field(child_name, child_data)
                    children.append(field_child)
                elif (
                    child_type
                    == "https://schema.metadatacenter.org/core/TemplateElement"
                ):
                    # It's an element
                    element_child = _transform_element(child_name, child_data)
                    children.append(element_child)
                elif child_data.get("type") == "array" and "items" in child_data:
                    # It's an array of elements
                    array_child = _transform_element(child_name, child_data)
                    children.append(array_child)

    return children


def clean_template_response(
    template_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Clean and transform the raw CEDAR template JSON-LD to simplified YAML structure.
    Now supports nested objects, arrays, and template elements.

    Args:
        template_data: Raw template data from CEDAR (JSON-LD format)

    Returns:
        Cleaned and transformed template data as dictionary (ready for YAML export)
    """
    # Extract template name, preferring schema:name for correct casing
    template_name = template_data.get("schema:name", "")
    if not template_name:
        # Fallback to title if schema:name is empty
        title = template_data.get("title", "")
        template_name = (
            title.replace(" template schema", "").replace("template schema", "").strip()
        )
        if not template_name:
            template_name = "Unnamed Template"

    # Get field order from UI configuration
    ui_config = template_data.get("_ui", {})
    field_order = ui_config.get("order", [])

    # Get properties section
    properties = template_data.get("properties", {})

    # Transform fields and elements in the specified order
    output_children: List[Union[FieldDefinition, ElementDefinition]] = []

    # Process fields/elements only in UI order since it covers all template items
    for item_name in field_order:
        if item_name in properties:
            item_data = properties[item_name]
            if isinstance(item_data, dict):
                item_type = item_data.get("@type", "")

                if item_type == "https://schema.metadatacenter.org/core/TemplateField":
                    # It's a simple field
                    field_child = _transform_field(item_name, item_data)
                    output_children.append(field_child)
                elif (
                    item_type
                    == "https://schema.metadatacenter.org/core/TemplateElement"
                ):
                    # It's a template element (possibly an array)
                    element_child = _transform_element(item_name, item_data)
                    output_children.append(element_child)
                elif item_data.get("type") == "array" and "items" in item_data:
                    # It's an array - check what type of items it contains
                    items_type = item_data["items"].get("@type", "")
                    if (
                        items_type
                        == "https://schema.metadatacenter.org/core/TemplateField"
                    ):
                        # Array of fields - treat as a field with array marker
                        field_child = _transform_field(item_name, item_data)
                        output_children.append(field_child)
                    elif (
                        items_type
                        == "https://schema.metadatacenter.org/core/TemplateElement"
                    ):
                        # Array of elements - treat as an element
                        element_child = _transform_element(item_name, item_data)
                        output_children.append(element_child)

    # Create output template
    output_template = SimplifiedTemplate(
        type="template", name=template_name, children=output_children
    )

    # Convert to dictionary for YAML export
    return output_template.model_dump(exclude_none=True)


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

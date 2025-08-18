#!/usr/bin/env python3

from typing import Any, Dict, List, Optional, Union

from .model import (
    ControlledTermValue,
    ControlledTermDefault,
    FieldConfiguration,
    FieldDefinition,
    SimplifiedTemplate
)
from .external_api import get_children_from_branch


def _determine_datatype(field_data: Dict[str, Any]) -> str:
    """
    Determine the appropriate datatype for a field based on its properties.
    
    Args:
        field_data: Field data from input JSON-LD
        
    Returns:
        Datatype string (string, integer, decimal, boolean)
    """
    properties = field_data.get('properties', {})
    value_props = properties.get('@value', {})
    
    # Check for numeric and boolean types
    if isinstance(value_props, dict) and 'type' in value_props:
        value_type = value_props['type']
        if value_type == 'number':
            return 'decimal'
        elif value_type == 'integer':
            return 'integer'
        elif value_type == 'boolean':
            return 'boolean'
    
    # Check if it's a list type that includes numbers
    if isinstance(value_props, dict) and 'type' in value_props:
        if isinstance(value_props['type'], list):
            if 'number' in value_props['type']:
                return 'decimal'
            elif 'integer' in value_props['type']:
                return 'integer'
            elif 'boolean' in value_props['type']:
                return 'boolean'
    
    # Default to string for text, controlled terms, links
    return 'string'


def _extract_controlled_term_values(field_data: Dict[str, Any], bioportal_api_key: str) -> Optional[List[ControlledTermValue]]:
    """
    Extract controlled term values from field constraints.
    
    The constraints are either literals or non-literals:
    - Literals: Simple text values, no IRIs needed
    - Non-literals: Ontology terms with IRIs from ontologies, valueSets, classes, or branches
    
    Args:
        field_data: Field data from input JSON-LD
        bioportal_api_key: BioPortal API key for fetching controlled term values
    Returns:
        List of controlled term values or None if not a controlled term field
    """
    constraints = field_data.get('_valueConstraints', {})
    
    # Check for different types of controlled vocabulary data
    literals = constraints.get('literals', [])
    ontologies = constraints.get('ontologies', [])
    value_sets = constraints.get('valueSets', [])
    classes = constraints.get('classes', [])
    branches = constraints.get('branches', [])
    default_value = constraints.get('defaultValue')
    
    # Check if this is a controlled term field
    has_controlled_terms = (
        literals or ontologies or value_sets or classes or branches
    )
    
    if not has_controlled_terms:
        return None
    
    # Handle literals (no IRIs needed)
    if literals:
        return [ControlledTermValue(label=literal['label']) 
                for literal in literals 
                if isinstance(literal, dict) and 'label' in literal]
    else: 
        # Handle non-literals (all must have IRIs)
        values_dict = {}  # Use dict to avoid duplicates by IRI
        
        # TODO: Handle ontologies (skipped for now)
        if ontologies:
            # TODO: Implement ontology processing
            pass
        
        # TODO: Handle valueSets (skipped for now)
        if value_sets:
            # TODO: Implement valueSet processing
            pass
        
        # Handle classes: pick name and IRI directly
        for class_item in classes:
            if isinstance(class_item, dict) and 'prefLabel' in class_item and '@id' in class_item:
                iri = class_item['@id']
                label = class_item['prefLabel']
                if iri not in values_dict:
                    values_dict[iri] = ControlledTermValue(label=label, iri=iri)
        
        # Handle branches: need to access BioPortal to get children
        for branch in branches:
            if isinstance(branch, dict) and 'name' in branch and 'uri' in branch:
                # Add the branch itself as a value
                branch_iri = branch['uri']
                ontology_acronym = branch['acronym']
                
                # Fetch children from BioPortal
                try:
                    bioportal_response = get_children_from_branch(branch_iri, ontology_acronym, bioportal_api_key)
                    
                    # Check for API errors first
                    if "error" in bioportal_response:
                        # Skip processing if there was an API error
                        continue
                    
                    # Parse the raw BioPortal response
                    collection = bioportal_response.get('collection', [])
                    
                    # Convert BioPortal response to ControlledTermValue objects
                    for item in collection:
                        if isinstance(item, dict):
                            child_label = item.get('prefLabel')
                            child_iri = item.get('@id')
                            
                            if child_label and child_iri and child_iri not in values_dict:
                                values_dict[child_iri] = ControlledTermValue(
                                    label=child_label,
                                    iri=child_iri
                                )
                except ValueError:
                    # If API key not found, skip BioPortal children fetching
                    pass
        
        # Add default value if it exists (for fields with termUri)
        if default_value and isinstance(default_value, dict):
            if 'rdfs:label' in default_value and 'termUri' in default_value:
                default_iri = default_value['termUri']
                default_label = default_value['rdfs:label']
                if default_iri not in values_dict:
                    values_dict[default_iri] = ControlledTermValue(
                        label=default_label,
                        iri=default_iri
                    )
        
        # Return list of unique values
        return list(values_dict.values()) if values_dict else None


def _extract_default_value(field_data: Dict[str, Any]) -> Optional[Union[ControlledTermDefault, str, int, float, bool]]:
    """
    Extract default value from field data.
    
    Args:
        field_data: Field data from input JSON-LD
        
    Returns:
        Default value or None
    """
    constraints = field_data.get('_valueConstraints', {})
    
    # Check for structured default value (controlled terms)
    default_value = constraints.get('defaultValue')
    if default_value and isinstance(default_value, dict):
        if 'rdfs:label' in default_value and 'termUri' in default_value:
            return ControlledTermDefault(
                label=default_value['rdfs:label'],
                iri=default_value['termUri']
            )
    
    # Check for simple default values
    if default_value is not None and not isinstance(default_value, dict):
        return default_value
    
    # Check for controlled term default in branches
    branches = constraints.get('branches', [])
    if branches:
        # Use the first branch as default if no other default found
        for branch in branches:
            if isinstance(branch, dict) and 'name' in branch and 'uri' in branch:
                return ControlledTermDefault(
                    label=branch['name'],
                    iri=branch['uri']
                )
    
    return None


def _transform_field(field_name: str, field_data: Dict[str, Any], bioportal_api_key: str) -> FieldDefinition:
    """
    Transform a single field from input JSON-LD to output structure.
    
    Args:
        field_name: Name of the field
        field_data: Field data from input JSON-LD
        bioportal_api_key: BioPortal API key for fetching controlled term values
    Returns:
        Transformed output field
    """
    # Extract basic field information
    name = field_data.get('schema:name', field_name)
    description = field_data.get('schema:description', '')
    pref_label = field_data.get('skos:prefLabel', name)
    
    # Determine datatype
    datatype = _determine_datatype(field_data)
    
    # Extract configuration
    constraints = field_data.get('_valueConstraints', {})
    required = constraints.get('requiredValue', False)
    configuration = FieldConfiguration(required=required)
    
    # Extract regex if present
    regex = constraints.get('regex')
    
    # Extract controlled term values
    values = _extract_controlled_term_values(field_data, bioportal_api_key)
    
    # Extract default value
    default = _extract_default_value(field_data)
    
    return FieldDefinition(
        name=name,
        description=description,
        prefLabel=pref_label,
        datatype=datatype,
        configuration=configuration,
        regex=regex,
        default=default,
        values=values
    )


def clean_template_response(template_data: Dict[str, Any], bioportal_api_key: str) -> Dict[str, Any]:
    """
    Clean and transform the raw CEDAR template JSON-LD to simplified YAML structure.
    
    Args:
        template_data: Raw template data from CEDAR (JSON-LD format)
        bioportal_api_key: BioPortal API key for fetching controlled term values
    Returns:
        Cleaned and transformed template data as dictionary (ready for YAML export)
    """
    # Extract template name, preferring schema:name for correct casing
    template_name = template_data.get('schema:name', '')
    if not template_name:
        # Fallback to title if schema:name is empty
        title = template_data.get('title', '')
        template_name = title.replace(' template schema', '').replace('template schema', '').strip()
        if not template_name:
            template_name = 'Unnamed Template'
    
    # Get field order from UI configuration
    ui_config = template_data.get('_ui', {})
    field_order = ui_config.get('order', [])
    
    # Get properties section
    properties = template_data.get('properties', {})
    
    # Transform fields in the specified order (field_order covers all CEDAR fields)
    output_fields = []
    
    # Process fields only in UI order since it covers all template fields
    for field_name in field_order:
        if field_name in properties:
            field_data = properties[field_name]
            if isinstance(field_data, dict) and '@type' in field_data:
                output_field = _transform_field(field_name, field_data, bioportal_api_key)
                output_fields.append(output_field)
    
    # Create output template
    output_template = SimplifiedTemplate(
        type="template",
        name=template_name,
        children=output_fields
    )
    
    # Convert to dictionary for YAML export
    return output_template.model_dump(exclude_none=True)


def clean_template_instance_response(instance_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and transform CEDAR template instance JSON-LD to simplified structure.
    
    Removes metadata fields and transforms JSON-LD specific attributes:
    - Removes: '@context', 'schema:isBasedOn', 'schema:name', 'schema:description', 
               'pav:createdOn', 'pav:createdBy', 'oslc:modifiedBy', '@id' from root
    - Transforms: '@id' → 'iri', 'rdfs:label' → 'label' throughout
    - Flattens: '@value' objects to their direct values
    
    Args:
        instance_data: Raw instance data from CEDAR (JSON-LD format)
        
    Returns:
        Cleaned and transformed instance data as dictionary
    """
    # Remove metadata fields from root level
    metadata_fields = {
        '@context', 'schema:isBasedOn', 'schema:name', 'schema:description',
        'pav:createdOn', 'pav:createdBy', 'oslc:modifiedBy', '@id'
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
    
    Args:
        obj: Any JSON-LD object (dict, list, or primitive)
        
    Returns:
        Transformed object with simplified structure
    """
    if isinstance(obj, dict):
        # Handle @value flattening first
        if '@value' in obj and len(obj) == 1:
            return obj['@value']
        
        # Transform dictionary
        transformed = {}
        for key, value in obj.items():
            # Transform key names
            if key == '@id':
                new_key = 'iri'
            elif key == 'rdfs:label':
                new_key = 'label'
            else:
                new_key = key
            
            # Recursively transform the value
            transformed[new_key] = _transform_jsonld_structure(value)
        
        return transformed
    
    elif isinstance(obj, list):
        # Transform each item in the list
        return [_transform_jsonld_structure(item) for item in obj]
    
    else:
        # Primitive types (str, int, float, bool, None) - return as-is
        return obj
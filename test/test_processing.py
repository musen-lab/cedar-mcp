#!/usr/bin/env python3

import pytest
from typing import Dict, Any
from src.cedar_mcp.processing import (
    _determine_datatype,
    _extract_controlled_term_values,
    _extract_default_value,
    _transform_field,
    clean_template_response,
    clean_template_instance_response,
)
from src.cedar_mcp.model import (
    ControlledTermValue,
    ControlledTermDefault,
    FieldDefinition,
)


@pytest.mark.unit
class TestDetermineDatatype:
    """Tests for _determine_datatype function."""

    def test_string_datatype_default(self):
        """Test that string is returned as default datatype."""
        field_data = {"properties": {"@value": {}}}
        result = _determine_datatype(field_data)
        assert result == "string"

    def test_integer_datatype(self):
        """Test integer datatype detection."""
        field_data = {"properties": {"@value": {"type": "integer"}}}
        result = _determine_datatype(field_data)
        assert result == "integer"

    def test_decimal_datatype(self):
        """Test decimal datatype detection."""
        field_data = {"properties": {"@value": {"type": "number"}}}
        result = _determine_datatype(field_data)
        assert result == "decimal"

    def test_boolean_datatype(self):
        """Test boolean datatype detection."""
        field_data = {"properties": {"@value": {"type": "boolean"}}}
        result = _determine_datatype(field_data)
        assert result == "boolean"

    def test_list_type_integer(self):
        """Test integer datatype from list type."""
        field_data = {"properties": {"@value": {"type": ["string", "integer"]}}}
        result = _determine_datatype(field_data)
        assert result == "integer"

    def test_list_type_number(self):
        """Test decimal datatype from list type."""
        field_data = {"properties": {"@value": {"type": ["string", "number"]}}}
        result = _determine_datatype(field_data)
        assert result == "decimal"

    def test_empty_field_data(self):
        """Test handling of empty field data."""
        result = _determine_datatype({})
        assert result == "string"


@pytest.mark.integration
class TestExtractControlledTermValues:
    """Tests for _extract_controlled_term_values function."""

    def test_extract_literal_values(
        self, bioportal_api_key: str, sample_field_data_with_literals: Dict[str, Any]
    ):
        """Test extraction of literal controlled term values."""
        result = _extract_controlled_term_values(
            sample_field_data_with_literals, bioportal_api_key
        )

        assert result is not None
        assert len(result) == 3
        assert all(isinstance(value, ControlledTermValue) for value in result)
        assert all(value.iri is None for value in result)  # Literals have no IRI

        labels = [value.label for value in result]
        assert "Option 1" in labels
        assert "Option 2" in labels
        assert "Option 3" in labels

    def test_extract_class_values(
        self, bioportal_api_key: str, sample_field_data_with_classes: Dict[str, Any]
    ):
        """Test extraction of class controlled term values."""
        result = _extract_controlled_term_values(
            sample_field_data_with_classes, bioportal_api_key
        )

        assert result is not None
        assert len(result) == 1
        assert result[0].label == "Sample Class"
        assert result[0].iri == "http://example.org/sample-class"

    def test_extract_branch_values(
        self, bioportal_api_key: str, sample_field_data_with_branches: Dict[str, Any]
    ):
        """Test extraction of branch controlled term values using real BioPortal API."""
        result = _extract_controlled_term_values(
            sample_field_data_with_branches, bioportal_api_key
        )

        # Result depends on actual BioPortal data
        if result is not None:
            assert all(isinstance(value, ControlledTermValue) for value in result)
            assert all(
                value.iri is not None for value in result
            )  # Branch children have IRIs
            assert all(value.label.strip() != "" for value in result)

    def test_no_constraints_returns_none(self, bioportal_api_key: str):
        """Test that fields without constraints return None."""
        field_data = {"schema:name": "Simple Field", "_valueConstraints": {}}
        result = _extract_controlled_term_values(field_data, bioportal_api_key)
        assert result is None

    def test_invalid_api_key_handles_gracefully(
        self, sample_field_data_with_branches: Dict[str, Any]
    ):
        """Test that invalid API key is handled gracefully for branches."""
        result = _extract_controlled_term_values(
            sample_field_data_with_branches, "invalid-key"
        )

        # Should not crash, may return empty or None
        assert result is None or isinstance(result, list)

    def test_mixed_constraints(self, bioportal_api_key: str):
        """Test field with both classes and branches."""
        field_data = {
            "_valueConstraints": {
                "classes": [
                    {"prefLabel": "Test Class", "@id": "http://example.org/test"}
                ],
                "branches": [
                    {
                        "name": "Test Branch",
                        "uri": "http://purl.bioontology.org/ontology/HRAVS/HRAVS_0000225",
                        "acronym": "HRAVS",
                    }
                ],
            }
        }

        result = _extract_controlled_term_values(field_data, bioportal_api_key)

        if result is not None:
            # Should contain class value
            class_labels = [
                v.label for v in result if v.iri == "http://example.org/test"
            ]
            assert len(class_labels) > 0
            assert "Test Class" in class_labels


@pytest.mark.unit
class TestExtractDefaultValue:
    """Tests for _extract_default_value function."""

    def test_extract_controlled_term_default(self):
        """Test extraction of controlled term default value."""
        field_data = {
            "_valueConstraints": {
                "defaultValue": {
                    "rdfs:label": "Default Term",
                    "termUri": "http://example.org/default",
                }
            }
        }

        result = _extract_default_value(field_data)

        assert isinstance(result, ControlledTermDefault)
        assert result.label == "Default Term"
        assert result.iri == "http://example.org/default"

    def test_extract_simple_default(self):
        """Test extraction of simple default values."""
        test_cases = [
            ({"_valueConstraints": {"defaultValue": "test string"}}, "test string"),
            ({"_valueConstraints": {"defaultValue": 42}}, 42),
            ({"_valueConstraints": {"defaultValue": 3.14}}, 3.14),
            ({"_valueConstraints": {"defaultValue": True}}, True),
        ]

        for field_data, expected in test_cases:
            result = _extract_default_value(field_data)
            assert result == expected

    def test_extract_branch_default(self):
        """Test extraction of branch as default value."""
        field_data = {
            "_valueConstraints": {
                "branches": [
                    {"name": "Default Branch", "uri": "http://example.org/branch"}
                ]
            }
        }

        result = _extract_default_value(field_data)

        assert isinstance(result, ControlledTermDefault)
        assert result.label == "Default Branch"
        assert result.iri == "http://example.org/branch"

    def test_no_default_returns_none(self):
        """Test that fields without defaults return None."""
        field_data = {"_valueConstraints": {}}
        result = _extract_default_value(field_data)
        assert result is None


@pytest.mark.integration
class TestTransformField:
    """Tests for _transform_field function."""

    def test_transform_simple_field(self, bioportal_api_key: str):
        """Test transformation of a simple field."""
        field_data = {
            "schema:name": "Test Field",
            "schema:description": "A test field",
            "skos:prefLabel": "Test Field Label",
            "_valueConstraints": {"requiredValue": True},
            "@type": "https://schema.metadatacenter.org/core/TemplateField",
        }

        result = _transform_field("test_field", field_data, bioportal_api_key)

        assert isinstance(result, FieldDefinition)
        assert result.name == "Test Field"
        assert result.description == "A test field"
        assert result.prefLabel == "Test Field Label"
        assert result.datatype == "string"
        assert result.configuration.required is True
        assert result.values is None
        assert result.default is None

    def test_transform_field_with_literals(
        self, bioportal_api_key: str, sample_field_data_with_literals: Dict[str, Any]
    ):
        """Test transformation of field with literal constraints."""
        result = _transform_field(
            "literal_field", sample_field_data_with_literals, bioportal_api_key
        )

        assert isinstance(result, FieldDefinition)
        assert result.values is not None
        assert len(result.values) == 3
        assert all(v.iri is None for v in result.values)

    def test_transform_field_with_branches(
        self, bioportal_api_key: str, sample_field_data_with_branches: Dict[str, Any]
    ):
        """Test transformation of field with branch constraints."""
        result = _transform_field(
            "branch_field", sample_field_data_with_branches, bioportal_api_key
        )

        assert isinstance(result, FieldDefinition)
        # Values may or may not be present depending on BioPortal response
        if result.values is not None:
            assert all(isinstance(v, ControlledTermValue) for v in result.values)

    def test_transform_field_with_regex(self, bioportal_api_key: str):
        """Test transformation of field with regex constraint."""
        field_data = {
            "schema:name": "Email Field",
            "schema:description": "Email address field",
            "skos:prefLabel": "Email",
            "_valueConstraints": {
                "requiredValue": True,
                "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            },
            "@type": "https://schema.metadatacenter.org/core/TemplateField",
        }

        result = _transform_field("email_field", field_data, bioportal_api_key)

        assert result.regex == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


@pytest.mark.integration
class TestCleanTemplateResponse:
    """Tests for clean_template_response function."""

    def test_clean_minimal_template(
        self, bioportal_api_key: str, sample_minimal_template_data: Dict[str, Any]
    ):
        """Test cleaning of minimal template data."""
        result = clean_template_response(
            sample_minimal_template_data, bioportal_api_key
        )

        assert isinstance(result, dict)
        assert result["type"] == "template"
        assert result["name"] == "Test Template"
        assert "children" in result
        assert len(result["children"]) == 2

        # Verify field order is preserved
        field_names = [field["name"] for field in result["children"]]
        assert field_names == ["Field 1", "Field 2"]

    def test_clean_template_with_schema_name(self, bioportal_api_key: str):
        """Test template cleaning with schema:name preference."""
        template_data = {
            "schema:name": "Proper Template Name",
            "title": "Template Title Schema",
            "_ui": {"order": []},
            "properties": {},
        }

        result = clean_template_response(template_data, bioportal_api_key)
        assert result["name"] == "Proper Template Name"

    def test_clean_template_fallback_title(self, bioportal_api_key: str):
        """Test template cleaning with title fallback."""
        template_data = {
            "title": "Fallback template schema",
            "_ui": {"order": []},
            "properties": {},
        }

        result = clean_template_response(template_data, bioportal_api_key)
        assert result["name"] == "Fallback"

    def test_clean_template_empty_name(self, bioportal_api_key: str):
        """Test template cleaning with empty names."""
        template_data = {
            "schema:name": "",
            "title": "",
            "_ui": {"order": []},
            "properties": {},
        }

        result = clean_template_response(template_data, bioportal_api_key)
        assert result["name"] == "Unnamed Template"


@pytest.mark.integration
class TestTransformElement:
    """Tests for _transform_element function."""

    def test_transform_simple_element(
        self, bioportal_api_key: str, sample_nested_template_element: Dict[str, Any]
    ):
        """Test transformation of a simple template element with nested fields."""
        from src.cedar_mcp.processing import _transform_element
        from src.cedar_mcp.model import ElementDefinition, FieldDefinition

        result = _transform_element(
            "resource_type", sample_nested_template_element, bioportal_api_key
        )

        assert isinstance(result, ElementDefinition)
        assert result.name == "Resource Type"
        assert result.description == "Information about the type of the resource being described with metadata."
        assert result.prefLabel == "Resource Type"
        assert result.datatype == "element"
        assert result.is_array is False
        assert len(result.children) == 2

        # Check that children are fields
        child_names = [child.name for child in result.children]
        assert "Resource Type Category" in child_names
        assert "Resource Type Detail" in child_names
        assert all(isinstance(child, FieldDefinition) for child in result.children)

    def test_transform_array_element(
        self, bioportal_api_key: str, sample_array_template_element: Dict[str, Any]
    ):
        """Test transformation of an array template element."""
        from src.cedar_mcp.processing import _transform_element
        from src.cedar_mcp.model import ElementDefinition, FieldDefinition

        result = _transform_element(
            "data_file_title", sample_array_template_element, bioportal_api_key
        )

        assert isinstance(result, ElementDefinition)
        assert result.name == "Data File Title"
        assert result.datatype == "element"
        assert result.is_array is True
        assert len(result.children) == 2

        # Check that children are fields from the items structure
        child_names = [child.name for child in result.children]
        assert "Data File Title" in child_names
        assert "Title Language" in child_names
        assert all(isinstance(child, FieldDefinition) for child in result.children)

    def test_process_element_children(self, bioportal_api_key: str):
        """Test processing of element children with mixed fields and elements."""
        from src.cedar_mcp.processing import _process_element_children
        from src.cedar_mcp.model import ElementDefinition, FieldDefinition

        element_data = {
            "_ui": {"order": ["simple_field", "nested_element"]},
            "properties": {
                "simple_field": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateField",
                    "schema:name": "Simple Field",
                    "schema:description": "A simple field",
                    "skos:prefLabel": "Simple Field",
                    "_valueConstraints": {"requiredValue": False}
                },
                "nested_element": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                    "schema:name": "Nested Element",
                    "schema:description": "A nested element",
                    "skos:prefLabel": "Nested Element",
                    "_valueConstraints": {"requiredValue": False},
                    "_ui": {"order": []},
                    "properties": {}
                }
            }
        }

        result = _process_element_children(element_data, bioportal_api_key)

        assert len(result) == 2
        assert isinstance(result[0], FieldDefinition)
        assert isinstance(result[1], ElementDefinition)
        assert result[0].name == "Simple Field"
        assert result[1].name == "Nested Element"


@pytest.mark.integration
class TestCleanTemplateResponseNested:
    """Tests for clean_template_response function with nested structures."""

    def test_clean_template_with_elements(
        self, bioportal_api_key: str, sample_nested_template_element: Dict[str, Any]
    ):
        """Test cleaning template with template elements."""
        template_data = {
            "schema:name": "Template With Elements",
            "_ui": {"order": ["resource_type"]},
            "properties": {"resource_type": sample_nested_template_element}
        }

        result = clean_template_response(template_data, bioportal_api_key)

        assert result["type"] == "template"
        assert result["name"] == "Template With Elements"
        assert len(result["children"]) == 1

        element = result["children"][0]
        assert element["name"] == "Resource Type"
        assert element["datatype"] == "element"
        assert element["is_array"] is False
        assert len(element["children"]) == 2

        # Verify nested fields
        child_names = [child["name"] for child in element["children"]]
        assert "Resource Type Category" in child_names
        assert "Resource Type Detail" in child_names

    def test_clean_template_with_array_elements(
        self, bioportal_api_key: str, sample_array_template_element: Dict[str, Any]
    ):
        """Test cleaning template with array elements."""
        template_data = {
            "schema:name": "Template With Arrays",
            "_ui": {"order": ["data_file_title"]},
            "properties": {"data_file_title": sample_array_template_element}
        }

        result = clean_template_response(template_data, bioportal_api_key)

        assert result["type"] == "template"
        assert result["name"] == "Template With Arrays"
        assert len(result["children"]) == 1

        element = result["children"][0]
        assert element["name"] == "Data File Title"
        assert element["datatype"] == "element"
        assert element["is_array"] is True
        assert len(element["children"]) == 2

        # Verify nested fields from array items
        child_names = [child["name"] for child in element["children"]]
        assert "Data File Title" in child_names
        assert "Title Language" in child_names

    def test_clean_complex_nested_template(
        self, bioportal_api_key: str, sample_complex_nested_template: Dict[str, Any]
    ):
        """Test cleaning of complex template with multiple nesting levels."""
        result = clean_template_response(sample_complex_nested_template, bioportal_api_key)

        assert result["type"] == "template"
        assert result["name"] == "Complex Nested Template"
        assert len(result["children"]) == 4

        # Check structure: Simple Field, Resource Type (element), Data File Title (array), Data File Spatial Coverage (nested array)
        children_by_name = {child["name"]: child for child in result["children"]}

        # Simple field
        simple_field = children_by_name["Simple Field"]
        assert simple_field["datatype"] == "string"
        assert "children" not in simple_field

        # Template element
        resource_type = children_by_name["Resource Type"]
        assert resource_type["datatype"] == "element"
        assert resource_type["is_array"] is False
        assert len(resource_type["children"]) == 2

        # Array element
        title_array = children_by_name["Data File Title"]
        assert title_array["datatype"] == "element"
        assert title_array["is_array"] is True
        assert len(title_array["children"]) == 2

        # Nested array element
        spatial_coverage = children_by_name["Data File Spatial Coverage"]
        assert spatial_coverage["datatype"] == "element"
        assert spatial_coverage["is_array"] is True
        assert len(spatial_coverage["children"]) == 3

        # Check that nested coverage is also an array element
        nested_children_by_name = {child["name"]: child for child in spatial_coverage["children"]}
        nested_coverage = nested_children_by_name["Nested Coverage"]
        assert nested_coverage["datatype"] == "element"
        assert nested_coverage["is_array"] is True
        assert len(nested_coverage["children"]) == 2

    def test_mixed_fields_and_elements(self, bioportal_api_key: str):
        """Test template with both simple fields and nested elements."""
        template_data = {
            "schema:name": "Mixed Template",
            "_ui": {"order": ["simple_field", "complex_element"]},
            "properties": {
                "simple_field": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateField",
                    "schema:name": "Simple Field",
                    "schema:description": "A simple field",
                    "skos:prefLabel": "Simple Field",
                    "_valueConstraints": {"requiredValue": False}
                },
                "complex_element": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                    "schema:name": "Complex Element",
                    "schema:description": "A complex element",
                    "skos:prefLabel": "Complex Element",
                    "_valueConstraints": {"requiredValue": False},
                    "_ui": {"order": ["nested_field"]},
                    "properties": {
                        "nested_field": {
                            "@type": "https://schema.metadatacenter.org/core/TemplateField",
                            "schema:name": "Nested Field",
                            "schema:description": "A nested field",
                            "skos:prefLabel": "Nested Field",
                            "_valueConstraints": {"requiredValue": True}
                        }
                    }
                }
            }
        }

        result = clean_template_response(template_data, bioportal_api_key)

        assert len(result["children"]) == 2
        
        # First child should be a simple field
        simple_child = result["children"][0]
        assert simple_child["name"] == "Simple Field"
        assert simple_child["datatype"] == "string"
        assert "children" not in simple_child

        # Second child should be an element with nested field
        complex_child = result["children"][1]
        assert complex_child["name"] == "Complex Element"
        assert complex_child["datatype"] == "element"
        assert complex_child["is_array"] is False
        assert len(complex_child["children"]) == 1
        assert complex_child["children"][0]["name"] == "Nested Field"
        assert complex_child["children"][0]["configuration"]["required"] is True


@pytest.mark.unit
class TestCleanTemplateResponseArrayFields:
    """Tests for clean_template_response function with array fields (arrays of TemplateFields)."""

    def test_clean_template_with_array_field(
        self, bioportal_api_key: str, sample_template_with_array_field: Dict[str, Any]
    ):
        """Test cleaning template with array field (array of TemplateFields)."""
        result = clean_template_response(sample_template_with_array_field, bioportal_api_key)

        assert result["type"] == "template"
        assert result["name"] == "Template with Array Field"
        assert len(result["children"]) == 2

        # Check structure
        children_by_name = {child["name"]: child for child in result["children"]}

        # Simple field should not be array
        simple_field = children_by_name["Simple Field"]
        assert simple_field["datatype"] == "string"
        assert simple_field["is_array"] is False
        assert "children" not in simple_field

        # Array field should be marked as array
        array_field = children_by_name["Notes"]
        assert array_field["name"] == "Notes"
        assert array_field["datatype"] == "string"
        assert array_field["is_array"] is True
        assert "children" not in array_field
        assert array_field["description"] == "Additional notes or comments about the resource."

    def test_array_field_properties(self, bioportal_api_key: str, sample_array_template_field: Dict[str, Any]):
        """Test that array field properties are correctly extracted from items structure."""
        template_data = {
            "schema:name": "Array Field Test",
            "_ui": {"order": ["notes_array"]},
            "properties": {"notes_array": sample_array_template_field}
        }

        result = clean_template_response(template_data, bioportal_api_key)
        
        assert len(result["children"]) == 1
        array_field = result["children"][0]
        
        # Verify properties extracted from items structure
        assert array_field["name"] == "Notes"
        assert array_field["description"] == "Additional notes or comments about the resource."
        assert array_field["prefLabel"] == "Notes"
        assert array_field["datatype"] == "string"
        assert array_field["is_array"] is True
        assert array_field["configuration"]["required"] is False

    def test_mixed_array_fields_and_elements(self, bioportal_api_key: str):
        """Test template with both array fields and array elements."""
        template_data = {
            "schema:name": "Mixed Arrays Template",
            "_ui": {"order": ["notes_array", "elements_array"]},
            "properties": {
                "notes_array": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "@type": "https://schema.metadatacenter.org/core/TemplateField",
                        "schema:name": "Notes",
                        "schema:description": "Array of note fields",
                        "skos:prefLabel": "Notes",
                        "_valueConstraints": {"requiredValue": False}
                    }
                },
                "elements_array": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                        "schema:name": "Complex Item",
                        "schema:description": "Array of complex elements",
                        "skos:prefLabel": "Complex Item",
                        "_ui": {"order": ["inner_field"]},
                        "properties": {
                            "inner_field": {
                                "@type": "https://schema.metadatacenter.org/core/TemplateField",
                                "schema:name": "Inner Field",
                                "schema:description": "Field inside element",
                                "skos:prefLabel": "Inner Field",
                                "_valueConstraints": {"requiredValue": True}
                            }
                        }
                    }
                }
            }
        }

        result = clean_template_response(template_data, bioportal_api_key)
        
        assert len(result["children"]) == 2
        children_by_name = {child["name"]: child for child in result["children"]}

        # Array field should be a simple array field
        notes_array = children_by_name["Notes"]
        assert notes_array["datatype"] == "string"
        assert notes_array["is_array"] is True
        assert "children" not in notes_array

        # Array element should be an array element with children
        elements_array = children_by_name["Complex Item"]
        assert elements_array["datatype"] == "element"
        assert elements_array["is_array"] is True
        assert len(elements_array["children"]) == 1
        assert elements_array["children"][0]["name"] == "Inner Field"


@pytest.mark.unit
class TestCleanTemplateInstanceResponse:
    """Tests for clean_template_instance_response function - core transformations."""

    def test_metadata_removal_and_transformations(self):
        """Test metadata removal and all core transformations."""
        sample_instance = {
            "@context": {"schema": "http://schema.org/"},
            "@id": "https://repo.metadatacenter.org/template-instances/test-id",
            "schema:isBasedOn": "https://repo.metadatacenter.org/templates/test-template",
            "schema:name": "Test Instance",
            "pav:createdOn": "2021-11-18T10:40:02-08:00",
            "cell_type": {
                "@id": "http://purl.obolibrary.org/obo/CL_1000412",
                "rdfs:label": "endothelial cell",
            },
            "is_ftu": {"@value": "No"},
            "doi": [
                {"@value": "doi:10.1038/s41467-019-10861-2"},
                {"@value": "doi:10.1038/s41586-020-2941-1"},
            ],
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Verify metadata fields removed
        metadata_fields = {
            "@context",
            "schema:isBasedOn",
            "schema:name",
            "pav:createdOn",
            "@id",
        }
        for field in metadata_fields:
            assert field not in cleaned

        # Verify @id → iri transformation
        assert (
            cleaned["cell_type"]["iri"] == "http://purl.obolibrary.org/obo/CL_1000412"
        )
        assert "@id" not in cleaned["cell_type"]

        # Verify rdfs:label → label transformation
        assert cleaned["cell_type"]["label"] == "endothelial cell"
        assert "rdfs:label" not in cleaned["cell_type"]

        # Verify @value flattening
        assert cleaned["is_ftu"] == "No"
        assert cleaned["doi"] == [
            "doi:10.1038/s41467-019-10861-2",
            "doi:10.1038/s41586-020-2941-1",
        ]

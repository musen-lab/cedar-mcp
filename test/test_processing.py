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

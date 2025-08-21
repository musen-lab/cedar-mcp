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
            "schema:description": "A test instance for unit testing",
            "pav:createdOn": "2021-11-18T10:40:02-08:00",
            "pav:createdBy": "https://metadatacenter.org/users/test-user",
            "pav:derivedFrom": "https://repo.metadatacenter.org/template-instances/parent-instance",
            "pav:lastUpdatedOn": "2021-11-18T11:40:02-08:00",
            "oslc:modifiedBy": "https://metadatacenter.org/users/test-user",
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
            "schema:description",
            "pav:createdOn",
            "pav:createdBy",
            "pav:derivedFrom",
            "oslc:modifiedBy",
            "@id",
        }
        for field in metadata_fields:
            assert field not in cleaned

        # Verify fields that should be preserved (not metadata)
        assert (
            "pav:lastUpdatedOn" in cleaned
        )  # This should be preserved as it's not in metadata_fields

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

    def test_nested_context_removal(self):
        """Test that @context fields are removed from nested objects and arrays."""
        sample_instance = {
            "Project Title": [
                {
                    "@context": {
                        "title": "http://purl.org/dc/elements/1.1/title",
                        "language": "http://def.isotc211.org/iso19115/2003/IdentificationInformation#MD_DataIdentification.language",
                    },
                    "title": {"@value": "Test Project Title"},
                    "language": {
                        "@id": "https://www.omg.org/spec/LCC/Languages/LaISO639-1-LanguageCodes/en",
                        "rdfs:label": "en",
                    },
                }
            ],
            "Principal Investigator": {
                "@context": {
                    "ORCID": "https://schema.metadatacenter.org/properties/ee24c19a-1bb5-4693-8775-52ab7716108c"
                },
                "ORCID": {"@value": "https://orcid.org/0000-0003-1791-3626"},
            },
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Verify nested @context fields are removed
        assert "@context" not in cleaned["Project Title"][0]
        assert "@context" not in cleaned["Principal Investigator"]

        # Verify other data is preserved and transformed correctly
        assert cleaned["Project Title"][0]["title"] == "Test Project Title"
        assert (
            cleaned["Project Title"][0]["language"]["iri"]
            == "https://www.omg.org/spec/LCC/Languages/LaISO639-1-LanguageCodes/en"
        )
        assert cleaned["Project Title"][0]["language"]["label"] == "en"
        assert (
            cleaned["Principal Investigator"]["ORCID"]
            == "https://orcid.org/0000-0003-1791-3626"
        )

    def test_template_element_instance_id_removal(self):
        """Test that @id fields containing template-element-instances are removed."""
        sample_instance = {
            "Project Title": [
                {
                    "title": {"@value": "Test Project"},
                    "@id": "https://repo.metadatacenter.org/template-element-instances/8f727c0b-4033-49b7-92da-de12a7141550",
                }
            ],
            "Principal Investigator": {
                "ORCID": {"@value": "https://orcid.org/0000-0003-1791-3626"},
                "@id": "https://repo.metadatacenter.org/template-element-instances/bcc6c4da-802a-4026-9718-8d439267febd",
            },
            "Data Steward": [
                {
                    "Focus": [{"@value": "research oriented"}],
                    "@id": "https://repo.metadatacenter.org/template-element-instances/75b76f22-5928-4ec4-a164-0b313afb2f4e",
                },
                {
                    "Focus": [{"@value": "infrastructure oriented"}]
                    # Note: This one has no @id field, which should work fine
                },
            ],
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Verify template-element-instance @id fields are removed
        assert "@id" not in cleaned["Project Title"][0]
        assert "iri" not in cleaned["Project Title"][0]
        assert "@id" not in cleaned["Principal Investigator"]
        assert "iri" not in cleaned["Principal Investigator"]
        assert "@id" not in cleaned["Data Steward"][0]
        assert "iri" not in cleaned["Data Steward"][0]

        # Verify other data is preserved and transformed correctly
        assert cleaned["Project Title"][0]["title"] == "Test Project"
        assert (
            cleaned["Principal Investigator"]["ORCID"]
            == "https://orcid.org/0000-0003-1791-3626"
        )
        assert cleaned["Data Steward"][0]["Focus"] == ["research oriented"]
        assert cleaned["Data Steward"][1]["Focus"] == ["infrastructure oriented"]

    def test_non_template_element_instance_id_preservation(self):
        """Test that @id fields NOT containing template-element-instances are preserved as iri."""
        sample_instance = {
            "Lead Institution": {
                "@id": "http://www.fair-data-collective.com/zonmw/projectadmin/MaastrichtUniversity",
                "rdfs:label": "Maastricht University",
            },
            "Province": [
                {
                    "@id": "http://www.fair-data-collective.com/zonmw/projectadmin/Limburg",
                    "rdfs:label": "Limburg",
                }
            ],
            "Country": [
                {
                    "@id": "http://purl.bioontology.org/ontology/MESH/D009426",
                    "rdfs:label": "Netherlands",
                }
            ],
            # Root level template-instances (not template-element-instances) should also be removed by root cleanup
            "nested_data": {
                "sub_item": {
                    "@id": "http://example.org/some-other-resource",
                    "rdfs:label": "Some Resource",
                }
            },
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Verify non-template-element-instance @id fields are transformed to iri
        assert (
            cleaned["Lead Institution"]["iri"]
            == "http://www.fair-data-collective.com/zonmw/projectadmin/MaastrichtUniversity"
        )
        assert cleaned["Lead Institution"]["label"] == "Maastricht University"
        assert "@id" not in cleaned["Lead Institution"]
        assert "rdfs:label" not in cleaned["Lead Institution"]

        assert (
            cleaned["Province"][0]["iri"]
            == "http://www.fair-data-collective.com/zonmw/projectadmin/Limburg"
        )
        assert cleaned["Province"][0]["label"] == "Limburg"
        assert "@id" not in cleaned["Province"][0]
        assert "rdfs:label" not in cleaned["Province"][0]

        assert (
            cleaned["Country"][0]["iri"]
            == "http://purl.bioontology.org/ontology/MESH/D009426"
        )
        assert cleaned["Country"][0]["label"] == "Netherlands"
        assert "@id" not in cleaned["Country"][0]
        assert "rdfs:label" not in cleaned["Country"][0]

        # Verify nested non-template-element-instance @id is also transformed
        assert (
            cleaned["nested_data"]["sub_item"]["iri"]
            == "http://example.org/some-other-resource"
        )
        assert cleaned["nested_data"]["sub_item"]["label"] == "Some Resource"
        assert "@id" not in cleaned["nested_data"]["sub_item"]
        assert "rdfs:label" not in cleaned["nested_data"]["sub_item"]

    def test_complex_nested_structure_with_context_and_ids(self):
        """Test a complex structure combining both @context and @id removal scenarios."""
        sample_instance = {
            "Funder Information": [
                {
                    "@context": {
                        "funderName": "https://schema.metadatacenter.org/properties/0eb27432-1ede-44a1-87c2-bed2081cab5c",
                        "Funder GRID reference": "https://schema.metadatacenter.org/properties/41a72a33-f1c7-4c0b-8b26-129bc1793ea8",
                    },
                    "funderName": {"@value": "ZonMw"},
                    "Funder GRID reference": {"@value": "grid.438427.e"},
                    "@id": "https://repo.metadatacenter.org/template-element-instances/c6eeacfd-8d80-4742-8ba2-d707802dd6a4",
                }
            ],
            "Project Partner Institution": [
                {
                    "@id": "http://www.fair-data-collective.com/zonmw/projectadmin/MaastrichtUniversityMedicalCentre"
                }
            ],
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Verify @context is removed from nested object
        assert "@context" not in cleaned["Funder Information"][0]

        # Verify template-element-instance @id is removed
        assert "@id" not in cleaned["Funder Information"][0]
        assert "iri" not in cleaned["Funder Information"][0]

        # Verify non-template-element-instance @id is transformed to iri
        assert (
            cleaned["Project Partner Institution"][0]["iri"]
            == "http://www.fair-data-collective.com/zonmw/projectadmin/MaastrichtUniversityMedicalCentre"
        )
        assert "@id" not in cleaned["Project Partner Institution"][0]

        # Verify @value flattening still works
        assert cleaned["Funder Information"][0]["funderName"] == "ZonMw"
        assert (
            cleaned["Funder Information"][0]["Funder GRID reference"] == "grid.438427.e"
        )

    def test_value_type_conversion(self):
        """Test that @value objects with @type are properly converted to appropriate types."""
        sample_instance = {
            # String values (should remain as string)
            "End date": {"@value": "2022-08-31", "@type": "xsd:date"},
            "Project Title": {"@value": "Test Project Title", "@type": "xsd:string"},
            "Description": {"@value": "This is a description", "@type": "xsd:string"},
            # Numeric values (should be converted to numbers)
            "Project duration": {"@value": "24", "@type": "xsd:decimal"},
            "Budget amount": {"@value": "100000.50", "@type": "xsd:float"},
            "Participant count": {"@value": "42", "@type": "xsd:integer"},
            "Priority level": {"@value": "5", "@type": "xsd:int"},
            "Max participants": {"@value": "1000", "@type": "xsd:long"},
            "Weight": {"@value": "98.76", "@type": "xsd:double"},
            # Boolean values
            "Is active": {"@value": "true", "@type": "xsd:boolean"},
            "Is completed": {"@value": "false", "@type": "xsd:boolean"},
            "Has funding": {"@value": "1", "@type": "xsd:boolean"},
            "Is public": {"@value": "0", "@type": "xsd:boolean"},
            # Single @value (no @type) should remain as-is
            "Simple field": {"@value": "simple value"},
            # Array with mixed types
            "Mixed values": [
                {"@value": "123", "@type": "xsd:integer"},
                {"@value": "test string", "@type": "xsd:string"},
                {"@value": "true", "@type": "xsd:boolean"},
            ],
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Verify string types remain as strings
        assert cleaned["End date"] == "2022-08-31"
        assert isinstance(cleaned["End date"], str)

        assert cleaned["Project Title"] == "Test Project Title"
        assert isinstance(cleaned["Project Title"], str)

        assert cleaned["Description"] == "This is a description"
        assert isinstance(cleaned["Description"], str)

        # Verify numeric type conversions
        assert cleaned["Project duration"] == 24.0
        assert isinstance(cleaned["Project duration"], float)

        assert cleaned["Budget amount"] == 100000.50
        assert isinstance(cleaned["Budget amount"], float)

        assert cleaned["Participant count"] == 42
        assert isinstance(cleaned["Participant count"], int)

        assert cleaned["Priority level"] == 5
        assert isinstance(cleaned["Priority level"], int)

        assert cleaned["Max participants"] == 1000
        assert isinstance(cleaned["Max participants"], int)

        assert cleaned["Weight"] == 98.76
        assert isinstance(cleaned["Weight"], float)

        # Verify boolean type conversions
        assert cleaned["Is active"] is True
        assert isinstance(cleaned["Is active"], bool)

        assert cleaned["Is completed"] is False
        assert isinstance(cleaned["Is completed"], bool)

        assert cleaned["Has funding"] is True
        assert isinstance(cleaned["Has funding"], bool)

        assert cleaned["Is public"] is False
        assert isinstance(cleaned["Is public"], bool)

        # Verify single @value without @type
        assert cleaned["Simple field"] == "simple value"
        assert isinstance(cleaned["Simple field"], str)

        # Verify array with mixed types
        assert cleaned["Mixed values"] == [123, "test string", True]
        assert isinstance(cleaned["Mixed values"][0], int)
        assert isinstance(cleaned["Mixed values"][1], str)
        assert isinstance(cleaned["Mixed values"][2], bool)

    def test_value_type_conversion_edge_cases(self):
        """Test edge cases for @value and @type conversion."""
        sample_instance = {
            # Invalid numeric values should fall back to original string
            "Invalid decimal": {"@value": "not-a-number", "@type": "xsd:decimal"},
            "Invalid integer": {"@value": "abc123", "@type": "xsd:integer"},
            # Boolean edge cases
            "Boolean uppercase": {"@value": "TRUE", "@type": "xsd:boolean"},
            "Boolean mixed case": {"@value": "False", "@type": "xsd:boolean"},
            # Objects with more than @value and @type should be processed normally
            "Complex object": {
                "@value": "some value",
                "@type": "xsd:string",
                "@id": "http://example.org/resource",
                "rdfs:label": "Some Label",
            },
            # Unknown XSD types should return value as-is
            "Unknown type": {"@value": "custom value", "@type": "custom:unknownType"},
        }

        cleaned = clean_template_instance_response(sample_instance)

        # Invalid numeric conversions should fall back to original string
        assert cleaned["Invalid decimal"] == "not-a-number"
        assert isinstance(cleaned["Invalid decimal"], str)

        assert cleaned["Invalid integer"] == "abc123"
        assert isinstance(cleaned["Invalid integer"], str)

        # Boolean case insensitive
        assert cleaned["Boolean uppercase"] is True
        assert isinstance(cleaned["Boolean uppercase"], bool)

        assert cleaned["Boolean mixed case"] is False
        assert isinstance(cleaned["Boolean mixed case"], bool)

        # Complex objects should not be flattened - should keep all transformed fields
        complex_obj = cleaned["Complex object"]
        assert "@value" not in complex_obj
        assert "@type" not in complex_obj
        assert complex_obj["iri"] == "http://example.org/resource"
        assert complex_obj["label"] == "Some Label"

        # Unknown types should return value as string
        assert cleaned["Unknown type"] == "custom value"
        assert isinstance(cleaned["Unknown type"], str)

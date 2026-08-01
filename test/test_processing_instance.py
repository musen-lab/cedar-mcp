#!/usr/bin/env python3

import pytest

from src.cedar_mcp.processing.instance import clean_template_instance_response


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

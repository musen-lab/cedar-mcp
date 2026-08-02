#!/usr/bin/env python3

import pytest

from src.cedar_mcp.processing.template_json import clean_template_response
from src.cedar_mcp.processing.template_yaml import (
    _extract_yaml_datatype,
    _extract_yaml_default_value,
    _extract_yaml_permissible_value_definitions,
    _transform_yaml_field,
    clean_template_yaml_response,
)
from src.cedar_mcp.model import (
    BranchConstraint,
    ClassConstraint,
    ControlledTermDefault,
    FieldDefinition,
    LiteralConstraint,
    OntologyConstraint,
)


@pytest.mark.unit
class TestExtractYamlDatatype:
    """Tests for _extract_yaml_datatype function."""

    def test_string_datatype_default(self):
        """Test that string is returned as default datatype."""
        result = _extract_yaml_datatype({"type": "text-field"})
        assert result == "string"

    def test_string_for_textarea(self):
        """Test that text area fields return string."""
        result = _extract_yaml_datatype({"type": "text-area-field"})
        assert result == "string"

    def test_integer_datatype_xsd_int(self):
        """Test integer datatype detection from xsd:int."""
        field_data = {"type": "numeric-field", "datatype": "xsd:int"}
        assert _extract_yaml_datatype(field_data) == "integer"

    def test_integer_datatype_xsd_long(self):
        """Test integer datatype detection from xsd:long."""
        field_data = {"type": "numeric-field", "datatype": "xsd:long"}
        assert _extract_yaml_datatype(field_data) == "integer"

    def test_decimal_datatype(self):
        """Test decimal datatype detection from xsd:decimal."""
        field_data = {"type": "numeric-field", "datatype": "xsd:decimal"}
        assert _extract_yaml_datatype(field_data) == "decimal"

    def test_decimal_datatype_default_numeric(self):
        """Test decimal is default for numeric without a datatype."""
        assert _extract_yaml_datatype({"type": "numeric-field"}) == "decimal"

    def test_date_datatype(self):
        """Test date datatype detection from xsd:date."""
        field_data = {"type": "temporal-field", "datatype": "xsd:date"}
        assert _extract_yaml_datatype(field_data) == "date"

    def test_time_datatype(self):
        """Test time datatype detection from xsd:time."""
        field_data = {"type": "temporal-field", "datatype": "xsd:time"}
        assert _extract_yaml_datatype(field_data) == "time"

    def test_datetime_datatype(self):
        """Test datetime is default for temporal fields."""
        field_data = {"type": "temporal-field", "datatype": "xsd:dateTime"}
        assert _extract_yaml_datatype(field_data) == "datetime"

    def test_link_datatype(self):
        """Test link datatype detection from link fields."""
        assert _extract_yaml_datatype({"type": "link-field"}) == "link"

    def test_boolean_datatype_for_bare_checkbox(self):
        """Test that a checkbox without values is treated as boolean."""
        assert _extract_yaml_datatype({"type": "checkbox-field"}) == "boolean"

    def test_checkbox_with_values_is_string(self):
        """Test that a checkbox with controlled values is not boolean."""
        field_data = {"type": "checkbox-field", "values": [{"label": "Yes"}]}
        assert _extract_yaml_datatype(field_data) == "string"

    def test_controlled_term_returns_string(self):
        """Test that controlled term fields return string, not iri."""
        field_data = {"type": "controlled-term-field", "datatype": "iri"}
        assert _extract_yaml_datatype(field_data) == "string"

    def test_empty_field_data(self):
        """Test that empty field data returns string."""
        assert _extract_yaml_datatype({}) == "string"


@pytest.mark.unit
class TestExtractYamlPermissibleValueDefinitions:
    """Tests for _extract_yaml_permissible_value_definitions function."""

    def test_extract_literal_values(self):
        """Test extraction of untyped literal options."""
        field_data = {
            "type": "radio-field",
            "values": [{"label": "Yes", "selected": True}, {"label": "No"}],
        }
        result = _extract_yaml_permissible_value_definitions(field_data)

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], LiteralConstraint)
        assert result[0].options == ["Yes", "No"]

    def test_extract_ontology_values(self):
        """Test extraction of ontology constraints."""
        field_data = {
            "values": [
                {
                    "type": "ontology",
                    "acronym": "ISO639-1",
                    "ontologyName": "ISO639-1",
                    "iri": "https://bioportal.bioontology.org/ontologies/ISO639-1",
                }
            ]
        }
        result = _extract_yaml_permissible_value_definitions(field_data)

        assert result is not None
        assert isinstance(result[0], OntologyConstraint)
        assert result[0].ontology_acronyms == ["ISO639-1"]

    def test_extract_value_set_values(self):
        """Test that value sets are folded into ontology constraints."""
        field_data = {
            "values": [
                {
                    "type": "valueSet",
                    "acronym": "HRAVS",
                    "valueSetName": "Area unit",
                    "iri": "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000161",
                }
            ]
        }
        result = _extract_yaml_permissible_value_definitions(field_data)

        assert result is not None
        assert isinstance(result[0], OntologyConstraint)
        assert result[0].ontology_acronyms == ["Area unit"]

    def test_extract_class_values(self):
        """Test extraction of class constraints."""
        field_data = {
            "values": [
                {
                    "type": "class",
                    "label": "Human",
                    "acronym": "LOINC",
                    "termType": "class",
                    "termLabel": "Homo Sapiens",
                    "iri": "http://purl.bioontology.org/ontology/LNC/LA19711-3",
                }
            ]
        }
        result = _extract_yaml_permissible_value_definitions(field_data)

        assert result is not None
        assert isinstance(result[0], ClassConstraint)
        assert result[0].options[0].label == "Homo Sapiens"
        assert (
            result[0].options[0].term_iri
            == "http://purl.bioontology.org/ontology/LNC/LA19711-3"
        )

    def test_extract_branch_values(self):
        """Test extraction of branch constraints."""
        field_data = {
            "values": [
                {
                    "type": "branch",
                    "ontologyName": "undefined (HRAVS)",
                    "acronym": "HRAVS",
                    "termLabel": "Dataset type",
                    "iri": "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000361",
                }
            ]
        }
        result = _extract_yaml_permissible_value_definitions(field_data)

        assert result is not None
        assert isinstance(result[0], BranchConstraint)
        assert result[0].ontology_acronym == "HRAVS"
        assert (
            result[0].branch_iri
            == "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000361"
        )

    def test_no_values_returns_none(self):
        """Test that a field without values returns None."""
        assert (
            _extract_yaml_permissible_value_definitions({"type": "text-field"}) is None
        )

    def test_extract_mixed_constraints(self):
        """Test extraction when several constraint kinds are present."""
        field_data = {
            "values": [
                {"label": "Other"},
                {"type": "ontology", "acronym": "NCIT", "ontologyName": "NCIT"},
                {
                    "type": "branch",
                    "acronym": "HRAVS",
                    "termLabel": "Analyte class",
                    "iri": "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000371",
                },
            ]
        }
        result = _extract_yaml_permissible_value_definitions(field_data)

        assert result is not None
        assert len(result) == 3
        assert isinstance(result[0], LiteralConstraint)
        assert isinstance(result[1], OntologyConstraint)
        assert isinstance(result[2], BranchConstraint)


@pytest.mark.unit
class TestExtractYamlDefaultValue:
    """Tests for _extract_yaml_default_value function."""

    def test_extract_controlled_term_default(self):
        """Test extraction of a value/label default pair."""
        field_data = {
            "default": {
                "value": "https://purl.humanatlas.io/vocab/hravs#HRAVS_0000310",
                "label": "RNAseq",
            }
        }
        result = _extract_yaml_default_value(field_data)

        assert isinstance(result, ControlledTermDefault)
        assert result.label == "RNAseq"
        assert result.iri == "https://purl.humanatlas.io/vocab/hravs#HRAVS_0000310"

    def test_extract_simple_default(self):
        """Test extraction of a plain scalar default."""
        field_data = {"default": "944e5fa0-f68b-4bdd-8664-74a3909429a9"}
        assert (
            _extract_yaml_default_value(field_data)
            == "944e5fa0-f68b-4bdd-8664-74a3909429a9"
        )

    def test_extract_numeric_default(self):
        """Test extraction of a numeric default."""
        assert _extract_yaml_default_value({"default": 42}) == 42

    def test_selected_literal_is_not_a_default(self):
        """Test that an option marked selected does not become the default."""
        field_data = {
            "type": "radio-field",
            "values": [{"label": "Yes", "selected": True}, {"label": "No"}],
        }

        # `selected` is a UI preselection, not a declared default
        assert _extract_yaml_default_value(field_data) is None

    def test_branch_is_not_a_default(self):
        """Test that a branch constraint does not become a default value."""
        field_data = {
            "values": [
                {
                    "type": "branch",
                    "acronym": "HRAVS",
                    "termLabel": "Analyte class",
                    "iri": "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000371",
                }
            ]
        }

        # A branch root names a category to pick from, not a value the field holds
        assert _extract_yaml_default_value(field_data) is None

    def test_declared_default_wins_over_branch(self):
        """Test that a declared default is still reported alongside a branch."""
        field_data = {
            "default": {
                "value": "https://purl.humanatlas.io/vocab/hravs#HRAVS_0000310",
                "label": "RNAseq",
            },
            "values": [
                {
                    "type": "branch",
                    "acronym": "HRAVS",
                    "termLabel": "Dataset type",
                    "iri": "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000361",
                }
            ],
        }
        result = _extract_yaml_default_value(field_data)

        assert isinstance(result, ControlledTermDefault)
        assert result.label == "RNAseq"

    def test_no_default_returns_none(self):
        """Test that a field with no default returns None."""
        assert _extract_yaml_default_value({"type": "text-field"}) is None


@pytest.mark.unit
class TestTransformYamlField:
    """Tests for _transform_yaml_field function."""

    def test_transform_simple_field(self):
        """Test transforming a plain text field."""
        field_data = {
            "key": "lab_id",
            "type": "text-field",
            "name": "lab_id",
            "description": "A locally assigned identifier",
            "prefLabel": "Lab ID",
        }
        result = _transform_yaml_field(field_data)

        assert isinstance(result, FieldDefinition)
        assert result.name == "lab_id"
        assert result.description == "A locally assigned identifier"
        assert result.label == "Lab ID"
        assert result.type == "string"
        assert result.required is False
        assert result.multivalued is False
        assert result.pattern is None

    def test_transform_field_with_regex(self):
        """Test that regex is carried over as the pattern."""
        field_data = {
            "type": "text-field",
            "name": "parent_sample_id",
            "regex": "^HBM\\d{3}$",
            "configuration": {"required": True},
        }
        result = _transform_yaml_field(field_data)

        assert result.pattern == "^HBM\\d{3}$"
        assert result.required is True

    def test_transform_multivalued_field(self):
        """Test that configuration.multiple marks the field as multivalued."""
        field_data = {
            "type": "text-field",
            "name": "Notes",
            "configuration": {"multiple": True, "minItems": 1},
        }
        assert _transform_yaml_field(field_data).multivalued is True

    def test_label_falls_back_to_name(self):
        """Test that a field without prefLabel uses its name as the label."""
        field_data = {"type": "text-field", "name": "lab_id"}
        assert _transform_yaml_field(field_data).label == "lab_id"

    def test_name_falls_back_to_key(self):
        """Test that a field without a name uses its key."""
        field_data = {"type": "text-field", "key": "lab_id"}
        assert _transform_yaml_field(field_data).name == "lab_id"


@pytest.mark.unit
class TestCleanTemplateYamlResponse:
    """Tests for clean_template_yaml_response function."""

    def test_clean_minimal_template(self):
        """Test cleaning a template with a single field."""
        template_data = {
            "type": "template",
            "name": "RNAseq",
            "description": "A sample template",
            "id": "https://repo.metadatacenter.org/templates/944e5fa0",
            "children": [
                {
                    "key": "lab_id",
                    "type": "text-field",
                    "name": "lab_id",
                    "description": "A locally assigned identifier",
                    "prefLabel": "Lab ID",
                }
            ],
        }
        result = clean_template_yaml_response(template_data)

        assert result["type"] == "template"
        assert result["name"] == "RNAseq"
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "lab_id"

    def test_clean_template_empty_name(self):
        """Test that a template with no name gets a placeholder."""
        result = clean_template_yaml_response({"type": "template", "children": []})
        assert result["name"] == "Unnamed Template"

    def test_clean_template_without_children(self):
        """Test that a template with no children key still cleans."""
        result = clean_template_yaml_response({"type": "template", "name": "Empty"})
        assert result["children"] == []

    def test_static_fields_are_skipped(self):
        """Test that layout-only static fields are dropped."""
        template_data = {
            "type": "template",
            "name": "RNAseq",
            "children": [
                {
                    "key": "assay_description",
                    "type": "static-rich-text",
                    "name": "assay_description",
                    "content": "<hr /><p>Some long styled paragraph</p>",
                },
                {"key": "lab_id", "type": "text-field", "name": "lab_id"},
            ],
        }
        result = clean_template_yaml_response(template_data)

        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "lab_id"

    def test_clean_template_with_nested_elements(self):
        """Test cleaning a template with nested elements."""
        template_data = {
            "type": "template",
            "name": "RADx Metadata Specification",
            "children": [
                {
                    "key": "Data File Title",
                    "type": "element",
                    "name": "Data File Title",
                    "description": "A name by which the Data File is known.",
                    "children": [
                        {
                            "key": "Data File Title",
                            "type": "text-field",
                            "name": "Data File Title",
                            "prefLabel": "Data File Title",
                            "configuration": {"required": True},
                        },
                        {
                            "key": "Shape",
                            "type": "element",
                            "name": "Shape",
                            "children": [
                                {
                                    "key": "Point Number",
                                    "type": "numeric-field",
                                    "name": "Point Number",
                                    "datatype": "xsd:int",
                                }
                            ],
                            "configuration": {"multiple": True, "minItems": 1},
                        },
                    ],
                    "configuration": {"multiple": True, "minItems": 1},
                }
            ],
        }
        result = clean_template_yaml_response(template_data)

        element = result["children"][0]
        assert element["type"] == "element"
        assert element["multivalued"] is True
        assert len(element["children"]) == 2

        field = element["children"][0]
        assert field["type"] == "string"
        assert field["required"] is True

        nested_element = element["children"][1]
        assert nested_element["type"] == "element"
        assert nested_element["multivalued"] is True
        assert nested_element["children"][0]["type"] == "integer"

    def test_children_without_type_are_skipped(self):
        """Test that entries with no type are ignored."""
        template_data = {
            "type": "template",
            "name": "RNAseq",
            "children": [
                {"key": "mystery", "name": "mystery"},
                {"key": "lab_id", "type": "text-field", "name": "lab_id"},
            ],
        }
        result = clean_template_yaml_response(template_data)

        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "lab_id"

    def test_output_matches_json_cleaner_shape(self):
        """Test that YAML and JSON-LD cleaning produce the same output shape."""
        yaml_template = {
            "type": "template",
            "name": "Test Template",
            "children": [
                {
                    "key": "field1",
                    "type": "text-field",
                    "name": "field1",
                    "description": "A field",
                    "prefLabel": "Field 1",
                    "configuration": {"required": True},
                }
            ],
        }
        json_template = {
            "schema:name": "Test Template",
            "_ui": {"order": ["field1"]},
            "properties": {
                "field1": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateField",
                    "schema:name": "field1",
                    "schema:description": "A field",
                    "skos:prefLabel": "Field 1",
                    "_ui": {"inputType": "textfield"},
                    "_valueConstraints": {"requiredValue": True},
                }
            },
        }

        assert clean_template_yaml_response(yaml_template) == clean_template_response(
            json_template
        )

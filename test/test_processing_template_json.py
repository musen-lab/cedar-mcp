#!/usr/bin/env python3

import pytest
from typing import Dict, Any
from src.cedar_mcp.processing.template_json import (
    _extract_datatype,
    _extract_default_value,
    _extract_permissible_value_definitions,
    _transform_field,
    clean_template_response,
)
from src.cedar_mcp.model import (
    BranchConstraint,
    ClassConstraint,
    ClassOption,
    ControlledTermDefault,
    FieldDefinition,
    LiteralConstraint,
    OntologyConstraint,
)


@pytest.mark.unit
class TestExtractDatatype:
    """Tests for _extract_datatype function."""

    def test_string_datatype_default(self):
        """Test that string is returned as default datatype."""
        field_data = {"_ui": {"inputType": "textfield"}}
        result = _extract_datatype(field_data)
        assert result == "string"

    def test_string_for_textarea(self):
        """Test that textarea input type returns string."""
        field_data = {"_ui": {"inputType": "textarea"}}
        result = _extract_datatype(field_data)
        assert result == "string"

    def test_integer_datatype_xsd_int(self):
        """Test integer datatype detection from xsd:int."""
        field_data = {
            "_ui": {"inputType": "numeric"},
            "_valueConstraints": {"numberType": "xsd:int"},
        }
        result = _extract_datatype(field_data)
        assert result == "integer"

    def test_integer_datatype_xsd_integer(self):
        """Test integer datatype detection from xsd:integer."""
        field_data = {
            "_ui": {"inputType": "numeric"},
            "_valueConstraints": {"numberType": "xsd:integer"},
        }
        result = _extract_datatype(field_data)
        assert result == "integer"

    def test_integer_datatype_xsd_long(self):
        """Test integer datatype detection from xsd:long."""
        field_data = {
            "_ui": {"inputType": "numeric"},
            "_valueConstraints": {"numberType": "xsd:long"},
        }
        result = _extract_datatype(field_data)
        assert result == "integer"

    def test_decimal_datatype(self):
        """Test decimal datatype detection from xsd:decimal."""
        field_data = {
            "_ui": {"inputType": "numeric"},
            "_valueConstraints": {"numberType": "xsd:decimal"},
        }
        result = _extract_datatype(field_data)
        assert result == "decimal"

    def test_decimal_datatype_default_numeric(self):
        """Test decimal is default for numeric without specific numberType."""
        field_data = {
            "_ui": {"inputType": "numeric"},
            "_valueConstraints": {},
        }
        result = _extract_datatype(field_data)
        assert result == "decimal"

    def test_datetime_datatype(self):
        """Test datetime datatype detection."""
        field_data = {
            "_ui": {"inputType": "temporal"},
            "_valueConstraints": {"temporalType": "xsd:dateTime"},
        }
        result = _extract_datatype(field_data)
        assert result == "datetime"

    def test_date_datatype(self):
        """Test date datatype detection."""
        field_data = {
            "_ui": {"inputType": "temporal"},
            "_valueConstraints": {"temporalType": "xsd:date"},
        }
        result = _extract_datatype(field_data)
        assert result == "date"

    def test_time_datatype(self):
        """Test time datatype detection."""
        field_data = {
            "_ui": {"inputType": "temporal"},
            "_valueConstraints": {"temporalType": "xsd:time"},
        }
        result = _extract_datatype(field_data)
        assert result == "time"

    def test_link_datatype(self):
        """Test link datatype detection."""
        field_data = {"_ui": {"inputType": "link"}}
        result = _extract_datatype(field_data)
        assert result == "link"

    def test_empty_field_data(self):
        """Test handling of empty field data."""
        result = _extract_datatype({})
        assert result == "string"

    def test_controlled_term_returns_string(self):
        """Test that controlled term fields return string."""
        field_data = {
            "_ui": {"inputType": "textfield"},
            "_valueConstraints": {
                "ontologies": [{"acronym": "CHEBI"}],
            },
        }
        result = _extract_datatype(field_data)
        assert result == "string"


@pytest.mark.unit
class TestExtractPermissibleValueDefinitions:
    """Tests for _extract_permissible_value_definitions function."""

    def test_extract_literal_values(
        self, sample_field_data_with_literals: Dict[str, Any]
    ):
        """Test extraction of literal constraints."""
        result = _extract_permissible_value_definitions(sample_field_data_with_literals)

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], LiteralConstraint)
        assert result[0].type == "literal"
        assert result[0].options == ["Option 1", "Option 2", "Option 3"]

    def test_extract_class_values(self, sample_field_data_with_classes: Dict[str, Any]):
        """Test extraction of class constraints."""
        result = _extract_permissible_value_definitions(sample_field_data_with_classes)

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], ClassConstraint)
        assert result[0].type == "class"
        assert len(result[0].options) == 1
        assert result[0].options[0].label == "Sample Class"
        assert result[0].options[0].term_iri == "http://example.org/sample-class"

    def test_extract_branch_values(
        self, sample_field_data_with_branches: Dict[str, Any]
    ):
        """Test extraction of branch constraints."""
        result = _extract_permissible_value_definitions(sample_field_data_with_branches)

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], BranchConstraint)
        assert result[0].type == "branch"
        assert result[0].ontology_acronym == "CHEBI"
        assert result[0].branch_iri == "http://purl.obolibrary.org/obo/CHEBI_23367"

    def test_extract_ontology_values(
        self, sample_field_data_with_ontologies: Dict[str, Any]
    ):
        """Test extraction of ontology constraints."""
        result = _extract_permissible_value_definitions(
            sample_field_data_with_ontologies
        )

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], OntologyConstraint)
        assert result[0].type == "ontology"
        assert result[0].ontology_acronyms == ["CHEBI", "GO"]

    def test_extract_value_set_values(
        self, sample_field_data_with_value_sets: Dict[str, Any]
    ):
        """Test extraction of valueSet constraints as OntologyConstraint."""
        result = _extract_permissible_value_definitions(
            sample_field_data_with_value_sets
        )

        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], OntologyConstraint)
        assert result[0].type == "ontology"
        assert result[0].ontology_acronyms == ["HRAVS"]

    def test_no_constraints_returns_none(self):
        """Test that fields without constraints return None."""
        field_data = {"schema:name": "Simple Field", "_valueConstraints": {}}
        result = _extract_permissible_value_definitions(field_data)
        assert result is None

    def test_extract_mixed_constraints(self):
        """Test field with both classes and branches returns multiple constraint objects."""
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

        result = _extract_permissible_value_definitions(field_data)

        assert result is not None
        assert len(result) == 2

        # First should be ClassConstraint
        class_constraint = result[0]
        assert isinstance(class_constraint, ClassConstraint)
        assert class_constraint.options[0].label == "Test Class"
        assert class_constraint.options[0].term_iri == "http://example.org/test"

        # Second should be BranchConstraint
        branch_constraint = result[1]
        assert isinstance(branch_constraint, BranchConstraint)
        assert branch_constraint.ontology_acronym == "HRAVS"
        assert (
            branch_constraint.branch_iri
            == "http://purl.bioontology.org/ontology/HRAVS/HRAVS_0000225"
        )


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

    def test_branch_is_not_a_default(self):
        """Test that a branch constraint does not become a default value."""
        field_data = {
            "_valueConstraints": {
                "branches": [
                    {"name": "Default Branch", "uri": "http://example.org/branch"}
                ]
            }
        }

        # A branch root names a category to pick from, not a value the field holds
        assert _extract_default_value(field_data) is None

    def test_declared_default_wins_over_branch(self):
        """Test that a declared default is still reported alongside a branch."""
        field_data = {
            "_valueConstraints": {
                "branches": [
                    {"name": "Default Branch", "uri": "http://example.org/branch"}
                ],
                "defaultValue": {
                    "rdfs:label": "Real Default",
                    "termUri": "http://example.org/real",
                },
            }
        }

        result = _extract_default_value(field_data)

        assert isinstance(result, ControlledTermDefault)
        assert result.label == "Real Default"
        assert result.iri == "http://example.org/real"

    def test_no_default_returns_none(self):
        """Test that fields without defaults return None."""
        field_data = {"_valueConstraints": {}}
        result = _extract_default_value(field_data)
        assert result is None


@pytest.mark.unit
class TestTransformField:
    """Tests for _transform_field function."""

    def test_transform_simple_field(self):
        """Test transformation of a simple field."""
        field_data = {
            "schema:name": "Test Field",
            "schema:description": "A test field",
            "skos:prefLabel": "Test Field Label",
            "_valueConstraints": {"requiredValue": True},
            "@type": "https://schema.metadatacenter.org/core/TemplateField",
        }

        result = _transform_field("test_field", field_data)

        assert isinstance(result, FieldDefinition)
        assert result.name == "Test Field"
        assert result.description == "A test field"
        assert result.label == "Test Field Label"
        assert result.type == "string"
        assert result.required is True
        assert result.permissible_values is None
        assert result.default_value is None

    def test_transform_field_with_literals(
        self, sample_field_data_with_literals: Dict[str, Any]
    ):
        """Test transformation of field with literal constraints."""
        result = _transform_field("literal_field", sample_field_data_with_literals)

        assert isinstance(result, FieldDefinition)
        assert result.permissible_values is not None
        assert len(result.permissible_values) == 1
        assert isinstance(result.permissible_values[0], LiteralConstraint)
        assert result.permissible_values[0].options == [
            "Option 1",
            "Option 2",
            "Option 3",
        ]

    def test_transform_field_with_branches(
        self, sample_field_data_with_branches: Dict[str, Any]
    ):
        """Test transformation of field with branch constraints."""
        result = _transform_field("branch_field", sample_field_data_with_branches)

        assert isinstance(result, FieldDefinition)
        assert result.permissible_values is not None
        assert len(result.permissible_values) == 1
        assert isinstance(result.permissible_values[0], BranchConstraint)
        assert result.permissible_values[0].ontology_acronym == "CHEBI"

    def test_transform_field_with_regex(self):
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

        result = _transform_field("email_field", field_data)

        assert result.pattern == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


@pytest.mark.unit
class TestCleanTemplateResponse:
    """Tests for clean_template_response function."""

    def test_clean_minimal_template(self, sample_minimal_template_data: Dict[str, Any]):
        """Test cleaning of minimal template data."""
        result = clean_template_response(sample_minimal_template_data)

        assert isinstance(result, dict)
        assert result["type"] == "template"
        assert result["name"] == "Test Template"
        assert "children" in result
        assert len(result["children"]) == 2

        # Verify field order is preserved
        field_names = [field["name"] for field in result["children"]]
        assert field_names == ["Field 1", "Field 2"]

    def test_clean_template_with_schema_name(self):
        """Test template cleaning with schema:name preference."""
        template_data = {
            "schema:name": "Proper Template Name",
            "title": "Template Title Schema",
            "_ui": {"order": []},
            "properties": {},
        }

        result = clean_template_response(template_data)
        assert result["name"] == "Proper Template Name"

    def test_clean_template_fallback_title(self):
        """Test template cleaning with title fallback."""
        template_data = {
            "title": "Fallback template schema",
            "_ui": {"order": []},
            "properties": {},
        }

        result = clean_template_response(template_data)
        assert result["name"] == "Fallback"

    def test_clean_template_empty_name(self):
        """Test template cleaning with empty names."""
        template_data = {
            "schema:name": "",
            "title": "",
            "_ui": {"order": []},
            "properties": {},
        }

        result = clean_template_response(template_data)
        assert result["name"] == "Unnamed Template"


@pytest.mark.unit
class TestTransformElement:
    """Tests for _transform_element function."""

    def test_transform_simple_element(
        self, sample_nested_template_element: Dict[str, Any]
    ):
        """Test transformation of a simple template element with nested fields."""
        from src.cedar_mcp.processing.template_json import _transform_element
        from src.cedar_mcp.model import ElementDefinition, FieldDefinition

        result = _transform_element("resource_type", sample_nested_template_element)

        assert isinstance(result, ElementDefinition)
        assert result.name == "Resource Type"
        assert (
            result.description
            == "Information about the type of the resource being described with metadata."
        )
        assert result.label == "Resource Type"
        assert result.type == "element"
        assert result.multivalued is False
        assert len(result.children) == 2

        # Check that children are fields
        child_names = [child.name for child in result.children]
        assert "Resource Type Category" in child_names
        assert "Resource Type Detail" in child_names
        assert all(isinstance(child, FieldDefinition) for child in result.children)

    def test_transform_array_element(
        self, sample_array_template_element: Dict[str, Any]
    ):
        """Test transformation of an array template element."""
        from src.cedar_mcp.processing.template_json import _transform_element
        from src.cedar_mcp.model import ElementDefinition, FieldDefinition

        result = _transform_element("data_file_title", sample_array_template_element)

        assert isinstance(result, ElementDefinition)
        assert result.name == "Data File Title"
        assert result.type == "element"
        assert result.multivalued is True
        assert len(result.children) == 2

        # Check that children are fields from the items structure
        child_names = [child.name for child in result.children]
        assert "Data File Title" in child_names
        assert "Title Language" in child_names
        assert all(isinstance(child, FieldDefinition) for child in result.children)

    def test_process_element_children(self):
        """Test processing of element children with mixed fields and elements."""
        from src.cedar_mcp.processing.template_json import _process_element_children
        from src.cedar_mcp.model import ElementDefinition, FieldDefinition

        element_data = {
            "_ui": {"order": ["simple_field", "nested_element"]},
            "properties": {
                "simple_field": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateField",
                    "schema:name": "Simple Field",
                    "schema:description": "A simple field",
                    "skos:prefLabel": "Simple Field",
                    "_valueConstraints": {"requiredValue": False},
                },
                "nested_element": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                    "schema:name": "Nested Element",
                    "schema:description": "A nested element",
                    "skos:prefLabel": "Nested Element",
                    "_valueConstraints": {"requiredValue": False},
                    "_ui": {"order": []},
                    "properties": {},
                },
            },
        }

        result = _process_element_children(element_data)

        assert len(result) == 2
        assert isinstance(result[0], FieldDefinition)
        assert isinstance(result[1], ElementDefinition)
        assert result[0].name == "Simple Field"
        assert result[1].name == "Nested Element"


@pytest.mark.unit
class TestCleanTemplateResponseNested:
    """Tests for clean_template_response function with nested structures."""

    def test_clean_template_with_elements(
        self, sample_nested_template_element: Dict[str, Any]
    ):
        """Test cleaning template with template elements."""
        template_data = {
            "schema:name": "Template With Elements",
            "_ui": {"order": ["resource_type"]},
            "properties": {"resource_type": sample_nested_template_element},
        }

        result = clean_template_response(template_data)

        assert result["type"] == "template"
        assert result["name"] == "Template With Elements"
        assert len(result["children"]) == 1

        element = result["children"][0]
        assert element["name"] == "Resource Type"
        assert element["type"] == "element"
        assert element["multivalued"] is False
        assert len(element["children"]) == 2

        # Verify nested fields
        child_names = [child["name"] for child in element["children"]]
        assert "Resource Type Category" in child_names
        assert "Resource Type Detail" in child_names

    def test_clean_template_with_array_elements(
        self, sample_array_template_element: Dict[str, Any]
    ):
        """Test cleaning template with array elements."""
        template_data = {
            "schema:name": "Template With Arrays",
            "_ui": {"order": ["data_file_title"]},
            "properties": {"data_file_title": sample_array_template_element},
        }

        result = clean_template_response(template_data)

        assert result["type"] == "template"
        assert result["name"] == "Template With Arrays"
        assert len(result["children"]) == 1

        element = result["children"][0]
        assert element["name"] == "Data File Title"
        assert element["type"] == "element"
        assert element["multivalued"] is True
        assert len(element["children"]) == 2

        # Verify nested fields from array items
        child_names = [child["name"] for child in element["children"]]
        assert "Data File Title" in child_names
        assert "Title Language" in child_names

    def test_clean_complex_nested_template(
        self, sample_complex_nested_template: Dict[str, Any]
    ):
        """Test cleaning of complex template with multiple nesting levels."""
        result = clean_template_response(sample_complex_nested_template)

        assert result["type"] == "template"
        assert result["name"] == "Complex Nested Template"
        assert len(result["children"]) == 4

        # Check structure: Simple Field, Resource Type (element), Data File Title (array), Data File Spatial Coverage (nested array)
        children_by_name = {child["name"]: child for child in result["children"]}

        # Simple field
        simple_field = children_by_name["Simple Field"]
        assert simple_field["type"] == "string"
        assert "children" not in simple_field

        # Template element
        resource_type = children_by_name["Resource Type"]
        assert resource_type["type"] == "element"
        assert resource_type["multivalued"] is False
        assert len(resource_type["children"]) == 2

        # Array element
        title_array = children_by_name["Data File Title"]
        assert title_array["type"] == "element"
        assert title_array["multivalued"] is True
        assert len(title_array["children"]) == 2

        # Nested array element
        spatial_coverage = children_by_name["Data File Spatial Coverage"]
        assert spatial_coverage["type"] == "element"
        assert spatial_coverage["multivalued"] is True
        assert len(spatial_coverage["children"]) == 3

        # Check that nested coverage is also an array element
        nested_children_by_name = {
            child["name"]: child for child in spatial_coverage["children"]
        }
        nested_coverage = nested_children_by_name["Nested Coverage"]
        assert nested_coverage["type"] == "element"
        assert nested_coverage["multivalued"] is True
        assert len(nested_coverage["children"]) == 2

    def test_mixed_fields_and_elements(self):
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
                    "_valueConstraints": {"requiredValue": False},
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
                            "_valueConstraints": {"requiredValue": True},
                        }
                    },
                },
            },
        }

        result = clean_template_response(template_data)

        assert len(result["children"]) == 2

        # First child should be a simple field
        simple_child = result["children"][0]
        assert simple_child["name"] == "Simple Field"
        assert simple_child["type"] == "string"
        assert "children" not in simple_child

        # Second child should be an element with nested field
        complex_child = result["children"][1]
        assert complex_child["name"] == "Complex Element"
        assert complex_child["type"] == "element"
        assert complex_child["multivalued"] is False
        assert len(complex_child["children"]) == 1
        assert complex_child["children"][0]["name"] == "Nested Field"
        assert complex_child["children"][0]["required"] is True


@pytest.mark.unit
class TestCleanTemplateResponseArrayFields:
    """Tests for clean_template_response function with array fields (arrays of TemplateFields)."""

    def test_clean_template_with_array_field(
        self, sample_template_with_array_field: Dict[str, Any]
    ):
        """Test cleaning template with array field (array of TemplateFields)."""
        result = clean_template_response(sample_template_with_array_field)

        assert result["type"] == "template"
        assert result["name"] == "Template with Array Field"
        assert len(result["children"]) == 2

        # Check structure
        children_by_name = {child["name"]: child for child in result["children"]}

        # Simple field should not be array
        simple_field = children_by_name["Simple Field"]
        assert simple_field["type"] == "string"
        assert simple_field["multivalued"] is False
        assert "children" not in simple_field

        # Array field should be marked as array
        array_field = children_by_name["Notes"]
        assert array_field["name"] == "Notes"
        assert array_field["type"] == "string"
        assert array_field["multivalued"] is True
        assert "children" not in array_field
        assert (
            array_field["description"]
            == "Additional notes or comments about the resource."
        )

    def test_array_field_properties(self, sample_array_template_field: Dict[str, Any]):
        """Test that array field properties are correctly extracted from items structure."""
        template_data = {
            "schema:name": "Array Field Test",
            "_ui": {"order": ["notes_array"]},
            "properties": {"notes_array": sample_array_template_field},
        }

        result = clean_template_response(template_data)

        assert len(result["children"]) == 1
        array_field = result["children"][0]

        # Verify properties extracted from items structure
        assert array_field["name"] == "Notes"
        assert (
            array_field["description"]
            == "Additional notes or comments about the resource."
        )
        assert array_field["label"] == "Notes"
        assert array_field["type"] == "string"
        assert array_field["multivalued"] is True
        assert array_field["required"] is False

    def test_mixed_array_fields_and_elements(self):
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
                        "_valueConstraints": {"requiredValue": False},
                    },
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
                                "_valueConstraints": {"requiredValue": True},
                            }
                        },
                    },
                },
            },
        }

        result = clean_template_response(template_data)

        assert len(result["children"]) == 2
        children_by_name = {child["name"]: child for child in result["children"]}

        # Array field should be a simple array field
        notes_array = children_by_name["Notes"]
        assert notes_array["type"] == "string"
        assert notes_array["multivalued"] is True
        assert "children" not in notes_array

        # Array element should be an array element with children
        elements_array = children_by_name["Complex Item"]
        assert elements_array["type"] == "element"
        assert elements_array["multivalued"] is True
        assert len(elements_array["children"]) == 1
        assert elements_array["children"][0]["name"] == "Inner Field"


@pytest.mark.unit
class TestBranchExpansion:
    """Tests for expanding branch constraints via the JSON-LD cleaner."""

    TEMPLATE = {
        "schema:name": "Test Template",
        "_ui": {"order": ["analyte_class"]},
        "properties": {
            "analyte_class": {
                "@type": "https://schema.metadatacenter.org/core/TemplateField",
                "schema:name": "analyte_class",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "acronym": "HRAVS",
                            "name": "Analyte class",
                            "uri": "https://purl.humanatlas.io/vocab/hravs#HRAVS_1000371",
                        }
                    ]
                },
            }
        },
    }

    TERMS = [
        ClassOption(label="DNA", term_iri="https://example.org/DNA"),
        ClassOption(label="RNA", term_iri="https://example.org/RNA"),
    ]

    def _fetch(self, branch_iri, ontology_acronym):
        return list(self.TERMS)

    def test_not_expanded_by_default(self):
        """Test that the JSON-LD cleaner leaves branches alone by default."""
        result = clean_template_response(
            self.TEMPLATE, fetch_branch_options=self._fetch
        )

        constraint = result["children"][0]["permissible_values"][0]
        assert "options" not in constraint
        assert constraint["ontology_acronym"] == "HRAVS"

    def test_labels_mode(self):
        """Test that "labels" lists child labels and drops the root."""
        result = clean_template_response(
            self.TEMPLATE, expand_branches="labels", fetch_branch_options=self._fetch
        )

        constraint = result["children"][0]["permissible_values"][0]
        assert constraint["options"] == ["DNA", "RNA"]
        assert "ontology_acronym" not in constraint
        assert "branch_iri" not in constraint

    def test_terms_mode(self):
        """Test that "terms" lists child labels with their IRIs."""
        result = clean_template_response(
            self.TEMPLATE, expand_branches="terms", fetch_branch_options=self._fetch
        )

        constraint = result["children"][0]["permissible_values"][0]
        assert constraint["options"] == [
            {"label": "DNA", "term_iri": "https://example.org/DNA"},
            {"label": "RNA", "term_iri": "https://example.org/RNA"},
        ]
        assert "branch_iri" not in constraint

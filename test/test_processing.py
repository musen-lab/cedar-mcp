#!/usr/bin/env python3

import pytest
from typing import Dict, Any
from src.cedar_mcp.processing import (
    _extract_datatype,
    _extract_permissible_value_definitions,
    _extract_default_value,
    _extract_yaml_datatype,
    _extract_yaml_default_value,
    _extract_yaml_permissible_value_definitions,
    _transform_field,
    _transform_yaml_field,
    clean_template_response,
    clean_template_instance_response,
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
        from src.cedar_mcp.processing import _transform_element
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
        from src.cedar_mcp.processing import _transform_element
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

    def test_extract_selected_literal_default(self):
        """Test that a literal marked selected becomes the default."""
        field_data = {
            "type": "radio-field",
            "values": [{"label": "Yes", "selected": True}, {"label": "No"}],
        }
        assert _extract_yaml_default_value(field_data) == "Yes"

    def test_extract_branch_default(self):
        """Test that the first branch is used when no default is given."""
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
        result = _extract_yaml_default_value(field_data)

        assert isinstance(result, ControlledTermDefault)
        assert result.label == "Analyte class"

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

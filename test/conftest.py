#!/usr/bin/env python3

import os
import pytest
from typing import Dict, Any
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test")


@pytest.fixture(scope="session")
def cedar_api_key() -> str:
    """Get CEDAR API key from environment."""
    api_key = os.getenv("CEDAR_API_KEY")
    if not api_key:
        pytest.skip("CEDAR_API_KEY not found in .env.test")
    return api_key


@pytest.fixture(scope="session")
def bioportal_api_key() -> str:
    """Get BioPortal API key from environment."""
    api_key = os.getenv("BIOPORTAL_API_KEY")
    if not api_key:
        pytest.skip("BIOPORTAL_API_KEY not found in .env.test")
    return api_key


@pytest.fixture
def sample_cedar_template_id() -> str:
    """Known stable CEDAR template ID for testing."""
    return (
        "https://repo.metadatacenter.org/templates/92c50790-81cb-4449-ac62-a82edb3ad4e1"
    )


@pytest.fixture
def sample_bioportal_branch() -> Dict[str, str]:
    """Known stable BioPortal branch for testing."""
    return {
        "branch_iri": "http://purl.obolibrary.org/obo/CHEBI_23367",
        "ontology_acronym": "CHEBI",
    }


@pytest.fixture
def sample_field_data_with_branches() -> Dict[str, Any]:
    """Sample field data containing branch constraints for testing."""
    return {
        "schema:name": "Test Field",
        "schema:description": "A test field with branch constraints",
        "skos:prefLabel": "Test Field Label",
        "_valueConstraints": {
            "requiredValue": False,
            "branches": [
                {
                    "name": "Sample Branch",
                    "uri": "http://purl.obolibrary.org/obo/CHEBI_23367",
                    "acronym": "CHEBI",
                }
            ],
        },
        "@type": "https://schema.metadatacenter.org/core/TemplateField",
    }


@pytest.fixture
def sample_field_data_with_classes() -> Dict[str, Any]:
    """Sample field data containing class constraints for testing."""
    return {
        "schema:name": "Test Class Field",
        "schema:description": "A test field with class constraints",
        "skos:prefLabel": "Test Class Field Label",
        "_valueConstraints": {
            "requiredValue": True,
            "classes": [
                {"prefLabel": "Sample Class", "@id": "http://example.org/sample-class"}
            ],
        },
        "@type": "https://schema.metadatacenter.org/core/TemplateField",
    }


@pytest.fixture
def sample_field_data_with_literals() -> Dict[str, Any]:
    """Sample field data containing literal constraints for testing."""
    return {
        "schema:name": "Test Literal Field",
        "schema:description": "A test field with literal constraints",
        "skos:prefLabel": "Test Literal Field Label",
        "_valueConstraints": {
            "requiredValue": False,
            "literals": [
                {"label": "Option 1"},
                {"label": "Option 2"},
                {"label": "Option 3"},
            ],
        },
        "@type": "https://schema.metadatacenter.org/core/TemplateField",
    }


@pytest.fixture
def sample_minimal_template_data() -> Dict[str, Any]:
    """Minimal template data structure for testing."""
    return {
        "schema:name": "Test Template",
        "title": "Test Template Schema",
        "_ui": {"order": ["field1", "field2"]},
        "properties": {
            "field1": {
                "schema:name": "Field 1",
                "schema:description": "First test field",
                "skos:prefLabel": "Field One",
                "_valueConstraints": {"requiredValue": True},
                "@type": "https://schema.metadatacenter.org/core/TemplateField",
            },
            "field2": {
                "schema:name": "Field 2",
                "schema:description": "Second test field",
                "skos:prefLabel": "Field Two",
                "_valueConstraints": {
                    "requiredValue": False,
                    "literals": [{"label": "Test Option"}],
                },
                "@type": "https://schema.metadatacenter.org/core/TemplateField",
            },
        },
    }

@pytest.fixture
def sample_nested_template_element() -> Dict[str, Any]:
    """Sample template element with nested fields for testing."""
    return {
        "@type": "https://schema.metadatacenter.org/core/TemplateElement",
        "schema:name": "Resource Type",
        "schema:description": "Information about the type of the resource being described with metadata.",
        "skos:prefLabel": "Resource Type",
        "_valueConstraints": {"requiredValue": False},
        "_ui": {
            "order": ["Resource Type Category", "Resource Type Detail"],
            "propertyLabels": {
                "Resource Type Category": "Resource Type Category",
                "Resource Type Detail": "Resource Type Detail"
            },
            "propertyDescriptions": {
                "Resource Type Category": "Categorical type of the resource being described.",
                "Resource Type Detail": "Brief free-text characterization of the type details."
            }
        },
        "properties": {
            "Resource Type Category": {
                "@type": "https://schema.metadatacenter.org/core/TemplateField",
                "schema:name": "Resource Type Category",
                "schema:description": "Categorical type of the resource being described.",
                "skos:prefLabel": "Resource Type Category",
                "_valueConstraints": {"requiredValue": False}
            },
            "Resource Type Detail": {
                "@type": "https://schema.metadatacenter.org/core/TemplateField",
                "schema:name": "Resource Type Detail",
                "schema:description": "Brief free-text characterization of the type details.",
                "skos:prefLabel": "Resource Type Detail",
                "_valueConstraints": {"requiredValue": False}
            }
        }
    }


@pytest.fixture
def sample_array_template_element() -> Dict[str, Any]:
    """Sample array template element with nested structure for testing."""
    return {
        "type": "array",
        "minItems": 1,
        "items": {
            "@type": "https://schema.metadatacenter.org/core/TemplateElement",
            "schema:name": "Data File Title",
            "schema:description": "A name or title by which the Data File being described is known.",
            "skos:prefLabel": "Data File Title",
            "_ui": {
                "order": ["Data File Title", "Title Language"],
                "propertyLabels": {
                    "Data File Title": "Data File Title",
                    "Title Language": "Title Language"
                },
                "propertyDescriptions": {
                    "Data File Title": "A name or title by which the Data File being described is known.",
                    "Title Language": "Language in which the Data File title is provided."
                }
            },
            "properties": {
                "Data File Title": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateField",
                    "schema:name": "Data File Title",
                    "schema:description": "A name or title by which the Data File being described is known.",
                    "skos:prefLabel": "Data File Title",
                    "_valueConstraints": {"requiredValue": True}
                },
                "Title Language": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateField",
                    "schema:name": "Title Language",
                    "schema:description": "Language in which the Data File title is provided.",
                    "skos:prefLabel": "Title Language",
                    "_valueConstraints": {"requiredValue": False}
                }
            }
        }
    }


@pytest.fixture
def sample_complex_nested_template() -> Dict[str, Any]:
    """Complex template with multiple levels of nesting and arrays for testing."""
    return {
        "schema:name": "Complex Nested Template",
        "title": "Complex Nested Template Schema",
        "_ui": {
            "order": ["Simple Field", "Resource Type", "Data File Title", "Data File Spatial Coverage"]
        },
        "properties": {
            "Simple Field": {
                "@type": "https://schema.metadatacenter.org/core/TemplateField",
                "schema:name": "Simple Field",
                "schema:description": "A simple field for testing",
                "skos:prefLabel": "Simple Field",
                "_valueConstraints": {"requiredValue": False}
            },
            "Resource Type": {
                "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                "schema:name": "Resource Type",
                "schema:description": "Information about the type of the resource.",
                "skos:prefLabel": "Resource Type",
                "_valueConstraints": {"requiredValue": False},
                "_ui": {
                    "order": ["Resource Type Category", "Resource Type Detail"],
                },
                "properties": {
                    "Resource Type Category": {
                        "@type": "https://schema.metadatacenter.org/core/TemplateField",
                        "schema:name": "Resource Type Category",
                        "schema:description": "Categorical type of the resource.",
                        "skos:prefLabel": "Resource Type Category",
                        "_valueConstraints": {"requiredValue": False}
                    },
                    "Resource Type Detail": {
                        "@type": "https://schema.metadatacenter.org/core/TemplateField",
                        "schema:name": "Resource Type Detail",
                        "schema:description": "Type details for the resource.",
                        "skos:prefLabel": "Resource Type Detail",
                        "_valueConstraints": {"requiredValue": False}
                    }
                }
            },
            "Data File Title": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                    "schema:name": "Data File Title",
                    "schema:description": "Title information for the data file.",
                    "skos:prefLabel": "Data File Title",
                    "_ui": {
                        "order": ["Title Text", "Title Language"],
                    },
                    "properties": {
                        "Title Text": {
                            "@type": "https://schema.metadatacenter.org/core/TemplateField",
                            "schema:name": "Title Text",
                            "schema:description": "The actual title text.",
                            "skos:prefLabel": "Title Text",
                            "_valueConstraints": {"requiredValue": True}
                        },
                        "Title Language": {
                            "@type": "https://schema.metadatacenter.org/core/TemplateField",
                            "schema:name": "Title Language",
                            "schema:description": "Language of the title.",
                            "skos:prefLabel": "Title Language",
                            "_valueConstraints": {"requiredValue": False}
                        }
                    }
                }
            },
            "Data File Spatial Coverage": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                    "schema:name": "Data File Spatial Coverage",
                    "schema:description": "Spatial coverage information.",
                    "skos:prefLabel": "Data File Spatial Coverage",
                    "_ui": {
                        "order": ["Latitude", "Longitude", "Nested Coverage"],
                    },
                    "properties": {
                        "Latitude": {
                            "@type": "https://schema.metadatacenter.org/core/TemplateField",
                            "schema:name": "Latitude",
                            "schema:description": "Latitude coordinate.",
                            "skos:prefLabel": "Latitude",
                            "_valueConstraints": {"requiredValue": False}
                        },
                        "Longitude": {
                            "@type": "https://schema.metadatacenter.org/core/TemplateField",
                            "schema:name": "Longitude",
                            "schema:description": "Longitude coordinate.",
                            "skos:prefLabel": "Longitude",
                            "_valueConstraints": {"requiredValue": False}
                        },
                        "Nested Coverage": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "@type": "https://schema.metadatacenter.org/core/TemplateElement",
                                "schema:name": "Nested Coverage",
                                "schema:description": "Nested coverage details.",
                                "skos:prefLabel": "Nested Coverage",
                                "_ui": {
                                    "order": ["Point Number", "Point Description"],
                                },
                                "properties": {
                                    "Point Number": {
                                        "@type": "https://schema.metadatacenter.org/core/TemplateField",
                                        "schema:name": "Point Number",
                                        "schema:description": "Sequential point number.",
                                        "skos:prefLabel": "Point Number",
                                        "_valueConstraints": {"requiredValue": False}
                                    },
                                    "Point Description": {
                                        "@type": "https://schema.metadatacenter.org/core/TemplateField",
                                        "schema:name": "Point Description",
                                        "schema:description": "Description of the point.",
                                        "skos:prefLabel": "Point Description",
                                        "_valueConstraints": {"requiredValue": False}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

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
        "https://repo.metadatacenter.org/templates/e019284e-48d1-4494-bc83-ddefd28dfbac"
    )


@pytest.fixture
def sample_cedar_template_instance_id() -> str:
    """Known stable CEDAR template ID for testing."""
    return "https://repo.metadatacenter.org/template-instances/60f3206f-13a6-42d3-9493-638681ea7f69"


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

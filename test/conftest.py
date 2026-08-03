#!/usr/bin/env python3

import os
from pathlib import Path

import pytest
from typing import Dict
from dotenv import load_dotenv

from cedar_mcp.cache import BioPortalCache

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
def tmp_cache(tmp_path: Path) -> BioPortalCache:
    """Provide a BioPortalCache backed by a temporary database."""
    return BioPortalCache(db_path=tmp_path / "test_cache.db", ttl_seconds=3600)


@pytest.fixture
def sample_cedar_template_id() -> str:
    """Known stable CEDAR template ID for testing."""
    return (
        "https://repo.metadatacenter.org/templates/92c50790-81cb-4449-ac62-a82edb3ad4e1"
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
def sample_bioportal_search_params() -> Dict[str, str]:
    """Known stable BioPortal search parameters for testing."""
    return {
        "search_string": "aspirin",
        "ontology_acronym": "CHEBI",
        "branch_iri": "http://purl.obolibrary.org/obo/CHEBI_23367",
    }

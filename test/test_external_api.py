#!/usr/bin/env python3

import pytest
from typing import Dict
from src.cedar_mcp.external_api import get_children_from_branch, search_instance_ids, get_instance


@pytest.mark.integration
class TestGetChildrenFromBranch:
    """Integration tests for get_children_from_branch function."""

    def test_get_children_valid_branch(self, bioportal_api_key: str, sample_bioportal_branch: Dict[str, str]):
        """Test fetching children from a valid BioPortal branch."""
        branch_iri = sample_bioportal_branch["branch_iri"]
        ontology_acronym = sample_bioportal_branch["ontology_acronym"]
        
        result = get_children_from_branch(branch_iri, ontology_acronym, bioportal_api_key)
        
        # Should not contain error
        assert "error" not in result
        
        # Should have collection with children
        assert "collection" in result
        assert isinstance(result["collection"], list)
        
        # If there are children, they should have required fields
        if result["collection"]:
            child = result["collection"][0]
            assert "@id" in child
            assert "prefLabel" in child
            assert isinstance(child["prefLabel"], str)
            assert child["prefLabel"].strip() != ""

    def test_get_children_invalid_branch_iri(self, bioportal_api_key: str):
        """Test fetching children with invalid branch IRI."""
        invalid_iri = "http://invalid.example.com/nonexistent"
        ontology_acronym = "HRAVS"
        
        result = get_children_from_branch(invalid_iri, ontology_acronym, bioportal_api_key)
        
        # Should return error for invalid IRI
        assert "error" in result
        assert "Failed to fetch children from BioPortal" in result["error"]

    def test_get_children_invalid_ontology(self, bioportal_api_key: str):
        """Test fetching children with invalid ontology acronym."""
        branch_iri = "http://purl.obolibrary.org/obo/CHEBI_23367"
        invalid_ontology = "NONEXISTENT_ONTOLOGY"
        
        result = get_children_from_branch(branch_iri, invalid_ontology, bioportal_api_key)
        
        # Should return error for invalid ontology
        assert "error" in result
        assert "Failed to fetch children from BioPortal" in result["error"]

    def test_get_children_invalid_api_key(self, sample_bioportal_branch: Dict[str, str]):
        """Test fetching children with invalid API key."""
        branch_iri = sample_bioportal_branch["branch_iri"]
        ontology_acronym = sample_bioportal_branch["ontology_acronym"]
        invalid_api_key = "invalid-api-key-12345"
        
        result = get_children_from_branch(branch_iri, ontology_acronym, invalid_api_key)
        
        # Should return error for invalid API key
        assert "error" in result
        assert "Failed to fetch children from BioPortal" in result["error"]

    def test_get_children_empty_parameters(self, bioportal_api_key: str):
        """Test fetching children with empty parameters."""
        result = get_children_from_branch("", "CHEBI", bioportal_api_key)
        assert "error" in result
        
        result = get_children_from_branch("http://example.com/test", "", bioportal_api_key)
        assert "error" in result

    def test_get_children_url_encoding(self, bioportal_api_key: str):
        """Test that special characters in IRI are properly URL encoded."""
        # Use IRI with special characters that need encoding
        branch_iri = "http://purl.obolibrary.org/obo/CHEBI_23367#special chars"
        ontology_acronym = "CHEBI"
        
        result = get_children_from_branch(branch_iri, ontology_acronym, bioportal_api_key)
        
        # Should handle URL encoding without raising exceptions
        # Result may be error (invalid IRI) but should not crash
        assert isinstance(result, dict)
        assert "error" in result or "collection" in result

    @pytest.mark.slow
    def test_get_children_response_structure(self, bioportal_api_key: str):
        """Test detailed response structure from BioPortal API."""
        # Use a known branch that should have children
        branch_iri = "http://purl.obolibrary.org/obo/CHEBI_23367"
        ontology_acronym = "CHEBI"
        
        result = get_children_from_branch(branch_iri, ontology_acronym, bioportal_api_key)
        
        if "error" not in result:
            # Verify BioPortal response structure
            assert "collection" in result
            
            # If there are children, verify their structure
            if result["collection"]:
                for child in result["collection"]:
                    assert isinstance(child, dict)
                    assert "@id" in child
                    assert "prefLabel" in child
                    
                    # Verify IRI format
                    assert child["@id"].startswith("http")
                    
                    # Verify prefLabel is non-empty string
                    assert isinstance(child["prefLabel"], str)
                    assert len(child["prefLabel"].strip()) > 0

    def test_get_children_multiple_ontologies(self, bioportal_api_key: str):
        """Test fetching children from different ontologies."""
        test_cases = [
            {
                "branch_iri": "http://purl.obolibrary.org/obo/CHEBI_23367",
                "ontology_acronym": "CHEBI"
            }
            # Add more test cases here if you have access to other ontologies
        ]
        
        for case in test_cases:
            result = get_children_from_branch(
                case["branch_iri"], 
                case["ontology_acronym"], 
                bioportal_api_key
            )
            
            # Should return valid response (either data or reasonable error)
            assert isinstance(result, dict)
            assert "error" in result or "collection" in result


class TestSearchInstanceIds:
    """Tests for search_instance_ids function."""
    
    def test_search_instances_basic_functionality(self, cedar_api_key: str):
        """Test basic search functionality."""
        template_id = "8b47bae6-db32-4b13-9d12-d012f0be9412"
        
        result = search_instance_ids(template_id, cedar_api_key, limit=2)
        
        # Should have expected structure
        assert "instance_ids" in result
        assert "pagination" in result
        assert isinstance(result["instance_ids"], list)
        assert isinstance(result["pagination"], dict)
        
        # Check pagination metadata structure
        pagination = result["pagination"]
        assert "total_count" in pagination
        assert "limit" in pagination
        assert "offset" in pagination
        assert "current_page" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert isinstance(pagination["total_count"], int)
        
        # Should have found instances (this template has many)
        if "error" not in result:
            assert pagination["total_count"] > 0
    
    def test_search_instances_invalid_api_key(self):
        """Test search with invalid API key."""
        result = search_instance_ids("8b47bae6-db32-4b13-9d12-d012f0be9412", "invalid-key", limit=2)
        assert "error" in result


class TestGetInstance:
    """Tests for get_instance function."""
    
    def test_get_instance_invalid_api_key(self):
        """Test fetching instance with invalid API key."""
        instance_id = "https://repo.metadatacenter.org/template-instances/test-id"
        result = get_instance(instance_id, "invalid-api-key")
        assert "error" in result



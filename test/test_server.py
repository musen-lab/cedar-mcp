#!/usr/bin/env python3

import pytest
from typing import Dict
from unittest.mock import patch
import requests
from src.cedar_mcp.external_api import search_instance_ids, get_instance
import sys
import io


@pytest.mark.integration
class TestGetTemplate:
    """Integration tests for get_template function from server.py."""

    def test_get_template_valid_id(
        self, cedar_api_key: str, sample_cedar_template_id: str
    ):
        """Test fetching a valid template from CEDAR."""
        # We need to test the actual MCP tool function
        # Since it's defined inside main(), we'll test by importing and running

        # Mock sys.argv to provide API keys
        with patch.object(sys, "argv", ["server.py", "--cedar-api-key", cedar_api_key]):
            # Capture stdout to prevent MCP server from running
            io.StringIO()

            # We'll test the function logic by extracting it
            # Since the function is defined inside main(), we need to test indirectly
            headers = {
                "Accept": "application/json",
                "Authorization": f"apiKey {cedar_api_key}",
            }

            from urllib.parse import quote

            encoded_template_id = quote(sample_cedar_template_id, safe="")
            base_url = (
                f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
            )

            try:
                response = requests.get(base_url, headers=headers, timeout=30)
                response.raise_for_status()
                template_data = response.json()

                # Should receive valid JSON-LD data
                assert isinstance(template_data, dict)
                assert "@context" in template_data or "properties" in template_data

                # Test that cleaning function works with real data
                from src.cedar_mcp.processing import clean_template_response
                cleaned_data = clean_template_response(template_data)
                # Verify cleaned response structure
                assert isinstance(cleaned_data, dict)
                assert cleaned_data["type"] == "template"
                assert "name" in cleaned_data
                assert "children" in cleaned_data
                assert isinstance(cleaned_data["children"], list)

            except requests.exceptions.RequestException as e:
                pytest.fail(f"Failed to fetch template: {str(e)}")

    def test_get_template_invalid_id(self, cedar_api_key: str):
        """Test fetching with invalid template ID."""
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        from urllib.parse import quote

        invalid_template_id = (
            "https://repo.metadatacenter.org/templates/nonexistent-template-id"
        )
        encoded_template_id = quote(invalid_template_id, safe="")
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        response = requests.get(base_url, headers=headers)

        # Should get 404 or other error status
        assert response.status_code != 200

    def test_get_template_invalid_api_key(self, sample_cedar_template_id: str):
        """Test fetching with invalid API key."""
        headers = {
            "Accept": "application/json",
            "Authorization": "apiKey invalid-key-12345",
        }

        from urllib.parse import quote

        encoded_template_id = quote(sample_cedar_template_id, safe="")
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        response = requests.get(base_url, headers=headers)

        # Should get 401 Unauthorized
        assert response.status_code == 401

    def test_cedar_api_endpoint_structure(self):
        """Test CEDAR API endpoint URL structure and parameters."""

        # Test URL encoding works correctly
        test_template_id = (
            "https://repo.metadatacenter.org/templates/test-id-with-special-chars!"
        )
        from urllib.parse import quote

        encoded_template_id = quote(test_template_id, safe="")

        # Should not contain unencoded special characters
        assert "!" not in encoded_template_id
        assert "%21" in encoded_template_id

        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        # Test that URL is well-formed
        assert base_url.startswith("https://resource.metadatacenter.org/templates/")

    @pytest.mark.slow
    def test_cedar_template_real_data_structure(
        self, cedar_api_key: str, sample_cedar_template_id: str
    ):
        """Test real CEDAR template data structure and content."""
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        from urllib.parse import quote

        encoded_template_id = quote(sample_cedar_template_id, safe="")
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        try:
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            template_data = response.json()

            # Verify CEDAR JSON-LD structure
            assert isinstance(template_data, dict)

            # Common CEDAR template fields
            if "@context" in template_data:
                assert isinstance(template_data["@context"], dict)

            if "properties" in template_data:
                assert isinstance(template_data["properties"], dict)

            if "_ui" in template_data:
                assert isinstance(template_data["_ui"], dict)
                if "order" in template_data["_ui"]:
                    assert isinstance(template_data["_ui"]["order"], list)

            # Should have schema metadata
            schema_fields = ["schema:name", "schema:description", "title"]
            has_schema_field = any(field in template_data for field in schema_fields)
            assert has_schema_field, "Template should have schema metadata"

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to fetch template for structure test: {str(e)}")

    def test_cedar_api_authentication_header(self, cedar_api_key: str):
        """Test CEDAR API authentication header format."""
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        # Verify header format matches CEDAR documentation
        auth_header = headers["Authorization"]
        assert auth_header.startswith("apiKey ")
        assert len(auth_header.split(" ")) == 2
        assert auth_header.split(" ")[1] == cedar_api_key


@pytest.mark.unit
class TestServerConfiguration:
    """Tests for server configuration and setup."""

    def test_command_line_argument_parsing(self):
        """Test command line argument parsing."""
        import argparse

        # Simulate the argument parser from server.py
        parser = argparse.ArgumentParser(description="CEDAR MCP Python Server")
        parser.add_argument("--cedar-api-key", type=str, help="CEDAR API key")
        parser.add_argument("--bioportal-api-key", type=str, help="BioPortal API key")

        # Test parsing with both arguments
        args = parser.parse_args(
            [
                "--cedar-api-key",
                "test-cedar-key",
                "--bioportal-api-key",
                "test-bioportal-key",
            ]
        )

        assert args.cedar_api_key == "test-cedar-key"
        assert args.bioportal_api_key == "test-bioportal-key"

    def test_api_key_validation_logic(self):
        """Test API key validation logic."""
        # Test the logic used in main() for API key validation

        # Case 1: Command line argument provided
        command_line_key = "cmd-key"
        env_key = "env-key"
        result_key = command_line_key or env_key
        assert result_key == "cmd-key"

        # Case 2: Only environment variable provided
        command_line_key = None
        env_key = "env-key"
        result_key = command_line_key or env_key
        assert result_key == "env-key"

        # Case 3: Neither provided
        command_line_key = None
        env_key = None
        result_key = command_line_key or env_key
        assert result_key is None


@pytest.mark.integration
class TestServerEnvironment:
    """Integration tests for server environment setup."""

    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        import os
        from pathlib import Path

        # First check if environment variables are already set (CI context)
        cedar_key = os.getenv("CEDAR_API_KEY")
        bioportal_key = os.getenv("BIOPORTAL_API_KEY")

        # If not set, try to load from .env.test (local development)
        if not cedar_key or not bioportal_key:
            env_file = Path(".env.test")
            if env_file.exists():
                from dotenv import load_dotenv

                load_dotenv(".env.test")
                cedar_key = os.getenv("CEDAR_API_KEY")
                bioportal_key = os.getenv("BIOPORTAL_API_KEY")
            else:
                pytest.skip(
                    "Neither environment variables nor .env.test file available"
                )

        assert cedar_key is not None, "CEDAR_API_KEY not found"
        assert bioportal_key is not None, "BIOPORTAL_API_KEY not found"
        assert len(cedar_key) > 0, "CEDAR_API_KEY is empty"
        assert len(bioportal_key) > 0, "BIOPORTAL_API_KEY is empty"


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_complete_template_processing_workflow(
        self, cedar_api_key: str, sample_cedar_template_id: str
    ):
        """Test complete workflow from CEDAR API to cleaned template."""
        # Step 1: Fetch from CEDAR API
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        from urllib.parse import quote

        encoded_template_id = quote(sample_cedar_template_id, safe="")
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        try:
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            raw_template = response.json()

            # Step 2: Clean and transform template
            from src.cedar_mcp.processing import clean_template_response

            cleaned_template = clean_template_response(raw_template)

            # Step 3: Verify complete transformation
            assert isinstance(cleaned_template, dict)
            assert "type" in cleaned_template
            assert "name" in cleaned_template
            assert "children" in cleaned_template

            # Step 4: Verify fields are properly transformed
            if cleaned_template["children"]:
                for field in cleaned_template["children"]:
                    assert "name" in field
                    assert "description" in field
                    assert "prefLabel" in field
                    assert "datatype" in field
                    assert "configuration" in field

                    # Configuration should have required field
                    assert "required" in field["configuration"]
                    assert isinstance(field["configuration"]["required"], bool)

        except requests.exceptions.RequestException as e:
            pytest.fail(f"End-to-end workflow failed: {str(e)}")

    @pytest.mark.integration
    def test_complete_template_instance_processing_workflow(
        self, cedar_api_key: str, sample_cedar_template_instance_id: str
    ):
        """Test complete workflow from CEDAR API to cleaned template instance."""
        # Step 1: Fetch template instance from CEDAR API
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        from urllib.parse import quote

        encoded_instance_id = quote(sample_cedar_template_instance_id, safe="")
        base_url = f"https://resource.metadatacenter.org/template-instances/{encoded_instance_id}"

        try:
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            raw_instance = response.json()

            # Step 2: Clean and transform template instance
            from src.cedar_mcp.processing import clean_template_instance_response

            cleaned_instance = clean_template_instance_response(raw_instance)

            # Step 3: Verify complete transformation
            assert isinstance(cleaned_instance, dict)

            # Verify root-level metadata removal
            root_metadata_fields = {
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
            for field in root_metadata_fields:
                assert field not in cleaned_instance, (
                    f"Root metadata field '{field}' should be removed"
                )

            # Step 4: Verify nested @context removal and template-element-instance @id removal
            def check_nested_structure(obj, path=""):
                """Recursively check that @context and template-element-instance @ids are removed."""
                if isinstance(obj, dict):
                    # Check no @context fields exist
                    assert "@context" not in obj, f"@context found at path: {path}"

                    # Check template-element-instance @id removal
                    if "@id" in obj:
                        id_value = obj["@id"]
                        assert "template-element-instances" not in id_value, (
                            f"template-element-instance @id found at path: {path}"
                        )

                    # Check for proper @id -> iri transformation
                    if "iri" in obj:
                        # Verify it's a proper IRI and not a template-element-instance
                        iri_value = obj["iri"]
                        assert isinstance(iri_value, str), (
                            f"iri should be string at path: {path}"
                        )
                        assert "template-element-instances" not in iri_value, (
                            f"template-element-instance iri found at path: {path}"
                        )

                    # Check for proper rdfs:label -> label transformation
                    assert "rdfs:label" not in obj, (
                        f"rdfs:label found at path: {path} (should be 'label')"
                    )

                    # Recursively check nested objects
                    for key, value in obj.items():
                        check_nested_structure(value, f"{path}.{key}" if path else key)

                elif isinstance(obj, list):
                    # Recursively check list items
                    for i, item in enumerate(obj):
                        check_nested_structure(
                            item, f"{path}[{i}]" if path else f"[{i}]"
                        )

            check_nested_structure(cleaned_instance)

            # Step 5: Verify @value flattening and type conversion
            def check_value_flattening_and_type_conversion(obj, path=""):
                """Recursively check that @value objects are properly flattened and type-converted."""
                if isinstance(obj, dict):
                    # Check for single-key @value objects (these should be flattened)
                    if len(obj) == 1 and "@value" in obj:
                        # This should not happen since these get flattened
                        assert False, (
                            f"Single @value object found at path: {path} (should be flattened)"
                        )

                    # Check that @value and @type objects are properly converted
                    if "@value" in obj or "@type" in obj:
                        assert False, (
                            f"@value or @type found at path: {path} (should be converted)"
                        )

                    # Recursively check nested objects
                    for key, value in obj.items():
                        check_value_flattening_and_type_conversion(
                            value, f"{path}.{key}" if path else key
                        )

                elif isinstance(obj, list):
                    # Recursively check list items
                    for i, item in enumerate(obj):
                        check_value_flattening_and_type_conversion(
                            item, f"{path}[{i}]" if path else f"[{i}]"
                        )

            check_value_flattening_and_type_conversion(cleaned_instance)

            # Step 6: Verify specific type conversions from real CEDAR data
            # Based on the known sample template instance data
            if "Project duration" in cleaned_instance:
                # Should be converted to numeric
                assert isinstance(cleaned_instance["Project duration"], (int, float))
                print(
                    f"Project duration: {cleaned_instance['Project duration']} (type: {type(cleaned_instance['Project duration'])})"
                )

            if "Start date" in cleaned_instance:
                # Should remain as string (xsd:date)
                assert isinstance(cleaned_instance["Start date"], str)
                print(
                    f"Start date: {cleaned_instance['Start date']} (type: {type(cleaned_instance['Start date'])})"
                )

            if "End date" in cleaned_instance:
                # Should remain as string (xsd:date)
                assert isinstance(cleaned_instance["End date"], str)
                print(
                    f"End date: {cleaned_instance['End date']} (type: {type(cleaned_instance['End date'])})"
                )

            # Step 7: Verify data integrity - check that important data fields are preserved
            # (This varies by template instance, but we can check for non-empty structure)
            assert len(cleaned_instance) > 0, "Cleaned instance should not be empty"

            # Log some sample fields for debugging (if needed)
            print(f"Cleaned instance has {len(cleaned_instance)} top-level fields")
            if cleaned_instance:
                sample_keys = list(cleaned_instance.keys())[:5]  # First 5 keys
                print(f"Sample field names: {sample_keys}")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"End-to-end template instance workflow failed: {str(e)}")

    @pytest.mark.slow
    def test_template_with_value_constraints(
        self, cedar_api_key: str, sample_cedar_template_id: str
    ):
        """Test template processing returns properly structured value constraints."""
        # Fetch a real template
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        from urllib.parse import quote

        encoded_template_id = quote(sample_cedar_template_id, safe="")
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        try:
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            raw_template = response.json()

            from src.cedar_mcp.processing import clean_template_response

            cleaned_template = clean_template_response(raw_template)

            # Look for fields with value constraints
            fields_with_values = [
                field
                for field in cleaned_template.get("children", [])
                if field.get("values") is not None
            ]

            # If there are controlled term fields, verify they're properly structured
            for field in fields_with_values:
                for constraint in field["values"]:
                    assert "type" in constraint
                    assert constraint["type"] in {
                        "literal",
                        "ontology",
                        "class",
                        "branch",
                    }

                    if constraint["type"] == "literal":
                        assert "options" in constraint
                        assert isinstance(constraint["options"], list)
                    elif constraint["type"] == "ontology":
                        assert "ontology_acronyms" in constraint
                        assert isinstance(constraint["ontology_acronyms"], list)
                    elif constraint["type"] == "class":
                        assert "options" in constraint
                        for opt in constraint["options"]:
                            assert "label" in opt
                            assert "term_iri" in opt
                    elif constraint["type"] == "branch":
                        assert "ontology_acronym" in constraint
                        assert "branch_iri" in constraint

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Value constraints integration test failed: {str(e)}")


@pytest.mark.integration
class TestGetInstancesBasedOnTemplate:
    """Integration tests for the complete get_instances_based_on_template MCP tool."""

    def test_get_instances_based_on_template_integration(self, cedar_api_key: str):
        """Test complete get_instances_based_on_template workflow with real API."""
        template_id = "8b47bae6-db32-4b13-9d12-d012f0be9412"

        # Step 1: Search for instances
        search_result = search_instance_ids(template_id, cedar_api_key, limit=3)

        if "error" in search_result:
            pytest.skip(f"Search failed: {search_result['error']}")

        if not search_result["instance_ids"]:
            pytest.skip("No instances found for testing")

        # Step 2: Fetch first 2 instances only for testing
        test_instance_ids = search_result["instance_ids"][:2]
        instances = []
        failed_instances = []

        for instance_id in test_instance_ids:
            instance_content = get_instance(instance_id, cedar_api_key)

            if "error" in instance_content:
                failed_instances.append(
                    {"instance_id": instance_id, "error": instance_content["error"]}
                )
            else:
                instances.append(instance_content)

        # Verify results
        assert len(instances) + len(failed_instances) == len(test_instance_ids)

        # At least some should succeed
        assert len(instances) > 0, "No instances were successfully fetched"

        # Verify instance structure before cleaning
        for instance in instances:
            assert "@id" in instance
            assert "schema:isBasedOn" in instance
            assert (
                instance["schema:isBasedOn"]
                == f"https://repo.metadatacenter.org/templates/{template_id}"
            )

        # Test cleaning integration
        from src.cedar_mcp.processing import clean_template_instance_response

        cleaned_instances = []
        for instance in instances:
            cleaned = clean_template_instance_response(instance)
            cleaned_instances.append(cleaned)

            # Verify cleaning worked
            metadata_fields = {"@context", "schema:isBasedOn", "schema:name", "@id"}
            for field in metadata_fields:
                assert field not in cleaned, f"Metadata field {field} should be removed"

        # Verify we have cleaned instances
        assert len(cleaned_instances) > 0
        assert all(isinstance(inst, dict) for inst in cleaned_instances)


@pytest.mark.integration
class TestTermSearchFromBranch:
    """Integration tests for term_search_from_branch MCP tool."""

    def test_term_search_from_branch_successful(
        self,
        bioportal_api_key: str,
        sample_bioportal_search_params: Dict[str, str],
    ):
        """Test term_search_from_branch returns results for a known term."""
        from src.cedar_mcp.external_api import search_terms_from_branch

        result = search_terms_from_branch(
            search_string=sample_bioportal_search_params["search_string"],
            ontology_acronym=sample_bioportal_search_params["ontology_acronym"],
            branch_iri=sample_bioportal_search_params["branch_iri"],
            bioportal_api_key=bioportal_api_key,
        )

        assert "error" not in result
        assert "collection" in result
        assert isinstance(result["collection"], list)
        assert len(result["collection"]) > 0

        # Verify result structure
        first_result = result["collection"][0]
        assert "@id" in first_result
        assert "prefLabel" in first_result

    def test_term_search_from_branch_empty_results(
        self,
        bioportal_api_key: str,
    ):
        """Test term_search_from_branch returns empty collection for nonsensical query."""
        from src.cedar_mcp.external_api import search_terms_from_branch

        result = search_terms_from_branch(
            search_string="xyznonexistentterm12345",
            ontology_acronym="CHEBI",
            branch_iri="http://purl.obolibrary.org/obo/CHEBI_23367",
            bioportal_api_key=bioportal_api_key,
        )

        assert "error" not in result
        assert "collection" in result
        assert isinstance(result["collection"], list)
        assert len(result["collection"]) == 0


@pytest.mark.integration
class TestTermSearchFromOntology:
    """Integration tests for term_search_from_ontology MCP tool."""

    def test_term_search_from_ontology_successful(
        self,
        bioportal_api_key: str,
    ):
        """Test term_search_from_ontology returns results for a known term."""
        from src.cedar_mcp.external_api import search_terms_from_ontology

        result = search_terms_from_ontology(
            search_string="melanoma",
            ontology_acronym="NCIT",
            bioportal_api_key=bioportal_api_key,
        )

        assert "error" not in result
        assert "collection" in result
        assert isinstance(result["collection"], list)
        assert len(result["collection"]) > 0

        # Verify result structure
        first_result = result["collection"][0]
        assert "@id" in first_result
        assert "prefLabel" in first_result

    def test_term_search_from_ontology_empty_results(
        self,
        bioportal_api_key: str,
    ):
        """Test term_search_from_ontology returns empty collection for nonsensical query."""
        from src.cedar_mcp.external_api import search_terms_from_ontology

        result = search_terms_from_ontology(
            search_string="xyznonexistentterm12345",
            ontology_acronym="NCIT",
            bioportal_api_key=bioportal_api_key,
        )

        assert "error" not in result
        assert "collection" in result
        assert isinstance(result["collection"], list)
        assert len(result["collection"]) == 0


@pytest.mark.integration
class TestGetChildrenFromBranch:
    """Integration tests for get_branch_children MCP tool."""

    def test_get_children_successful(
        self,
        bioportal_api_key: str,
        sample_bioportal_branch: Dict[str, str],
    ):
        """Test get_children_from_branch returns children for a known branch."""
        from src.cedar_mcp.external_api import get_children_from_branch

        result = get_children_from_branch(
            branch_iri=sample_bioportal_branch["branch_iri"],
            ontology_acronym=sample_bioportal_branch["ontology_acronym"],
            bioportal_api_key=bioportal_api_key,
        )

        assert "error" not in result
        assert "collection" in result
        assert isinstance(result["collection"], list)
        assert len(result["collection"]) > 0

        # Verify result structure
        first_result = result["collection"][0]
        assert "prefLabel" in first_result

    def test_get_children_invalid_branch(
        self,
        bioportal_api_key: str,
    ):
        """Test get_children_from_branch returns error for invalid branch IRI."""
        from src.cedar_mcp.external_api import get_children_from_branch

        result = get_children_from_branch(
            branch_iri="http://example.org/nonexistent/branch",
            ontology_acronym="CHEBI",
            bioportal_api_key=bioportal_api_key,
        )

        assert "error" in result

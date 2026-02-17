#!/usr/bin/env python3

import argparse
import os
import sys
from typing import Any, Dict
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

from .processing import clean_template_response, clean_template_instance_response
from .external_api import (
    get_children_from_branch,
    get_instance,
    search_instance_ids,
    search_terms_from_branch,
    search_terms_from_ontology,
)


def main():
    """Entry point for the cedar-mcp CLI."""
    # Load environment variables
    load_dotenv()

    # Create an MCP server
    mcp = FastMCP("cedar-mcp")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="CEDAR MCP Python Server")
    parser.add_argument(
        "--cedar-api-key",
        type=str,
        help="CEDAR API key to use instead of environment variable",
    )
    parser.add_argument(
        "--bioportal-api-key",
        type=str,
        help="BioPortal API key to use instead of environment variable",
    )
    args = parser.parse_args()

    # Use command-line argument if provided, otherwise use environment variable
    CEDAR_API_KEY = args.cedar_api_key or os.getenv("CEDAR_API_KEY")
    if not CEDAR_API_KEY:
        print(
            "Error: CEDAR API key not provided. Please set CEDAR_API_KEY environment variable or use --cedar-api-key."
        )
        sys.exit(1)

    BIOPORTAL_API_KEY = args.bioportal_api_key or os.getenv("BIOPORTAL_API_KEY")
    if not BIOPORTAL_API_KEY:
        print(
            "Error: BioPortal API key not provided. Please set BIOPORTAL_API_KEY environment variable or use --bioportal-api-key."
        )
        sys.exit(1)

    # Register MCP tools
    @mcp.tool()
    def get_template(template_id: str) -> Dict[str, Any]:
        """
        Get a template from the CEDAR repository.

        Args:
            template_id: The template ID or full URL from CEDAR repository
                        (e.g., "https://repo.metadatacenter.org/templates/e019284e-48d1-4494-bc83-ddefd28dfbac")

        Returns:
            Template data from CEDAR, cleaned and transformed
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {CEDAR_API_KEY}",
        }

        # Encode the template ID for URL
        encoded_template_id = quote(template_id, safe="")

        # Build the URL with a simple query parameter
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        try:
            response = requests.get(base_url, headers=headers)
            response.raise_for_status()
            template_data = response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch CEDAR template: {str(e)}"}

        # Always clean the response
        template_data = clean_template_response(template_data, BIOPORTAL_API_KEY)

        return template_data

    @mcp.tool()
    def get_instances_based_on_template(
        template_id: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get template instances that belong to the input template ID with pagination support.

        This tool searches for instances of a given template and fetches their complete content
        in paginated chunks to avoid token limit issues.

        Args:
            template_id: The template ID or full URL from CEDAR repository
                        (e.g., "https://repo.metadatacenter.org/templates/e019284e-48d1-4494-bc83-ddefd28dfbac")
            limit: Number of instances to return per page (min: 1, max: 100, default: 10)
            offset: Starting position for pagination (default: 0)

        Returns:
            Dictionary containing:
            - instances: List of template instances for this page
            - pagination: Pagination metadata (total_count, current_page, etc.)
            - errors: List of any errors encountered during fetching
        """
        # Validate pagination parameters
        if limit < 1 or limit > 100:
            return {
                "error": "Invalid limit parameter. Must be between 1 and 100.",
                "instances": [],
                "pagination": None,
            }

        if offset < 0:
            return {
                "error": "Invalid offset parameter. Must be 0 or greater.",
                "instances": [],
                "pagination": None,
            }

        # Step 1: Search for instance IDs with pagination
        search_result = search_instance_ids(
            template_id=template_id,
            cedar_api_key=CEDAR_API_KEY,
            limit=limit,
            offset=offset,
        )

        # Check if search failed
        if "error" in search_result:
            return {
                "error": f"Failed to search for template instances: {search_result['error']}",
                "instances": [],
                "pagination": None,
            }

        instance_ids = search_result.get("instance_ids", [])
        pagination_metadata = search_result.get("pagination", {})

        # If no instances found, return empty result with pagination metadata
        if not instance_ids:
            return {"instances": [], "pagination": pagination_metadata, "errors": None}

        # Step 2: Fetch content for each instance in this page
        instances = []
        failed_instances = []

        for instance_id in instance_ids:
            instance_content = get_instance(instance_id, CEDAR_API_KEY)

            # Check if this instance fetch failed
            if "error" in instance_content:
                failed_instances.append(
                    {"instance_id": instance_id, "error": instance_content["error"]}
                )
            else:
                # Clean the instance content before adding to results
                try:
                    cleaned_instance = clean_template_instance_response(
                        instance_content
                    )
                    instances.append(cleaned_instance)
                except Exception as e:
                    failed_instances.append(
                        {
                            "instance_id": instance_id,
                            "error": f"Failed to clean instance response: {str(e)}",
                        }
                    )

        # Step 3: Prepare response
        response = {"instances": instances, "pagination": pagination_metadata}

        # Include error information if any instances failed to fetch
        if failed_instances:
            response["errors"] = failed_instances

        return response

    @mcp.tool()
    def term_search_from_branch(
        search_string: str,
        ontology_acronym: str,
        branch_iri: str,
    ) -> Dict[str, Any]:
        """
        Search BioPortal for standardized ontology terms within a specific branch.

        Use this tool to find the correct standardized name and IRI for a given
        term label within a specific ontology branch.

        Args:
            search_string: The term label or keyword to search for
                          (e.g., "aspirin", "glucose")
            ontology_acronym: Ontology acronym to search within
                             (e.g., "CHEBI", "HRAVS")
            branch_iri: IRI of the branch to restrict the search to
                       (e.g., "http://purl.obolibrary.org/obo/CHEBI_23367")

        Returns:
            Search results from BioPortal containing matching terms
        """
        result = search_terms_from_branch(
            search_string=search_string,
            ontology_acronym=ontology_acronym,
            branch_iri=branch_iri,
            bioportal_api_key=BIOPORTAL_API_KEY,
        )

        if "error" in result:
            return {"error": f"Term search failed: {result['error']}"}

        return result

    @mcp.tool()
    def term_search_from_ontology(
        search_string: str,
        ontology_acronym: str,
    ) -> Dict[str, Any]:
        """
        Search BioPortal for standardized ontology terms within an entire ontology.

        Use this tool to find the correct standardized name and IRI for a given
        term label across an entire ontology (not restricted to a specific branch).

        Args:
            search_string: The term label or keyword to search for
                          (e.g., "melanoma", "diabetes")
            ontology_acronym: Ontology acronym to search within
                             (e.g., "NCIT", "CHEBI", "DOID")

        Returns:
            Search results from BioPortal containing matching terms
        """
        result = search_terms_from_ontology(
            search_string=search_string,
            ontology_acronym=ontology_acronym,
            bioportal_api_key=BIOPORTAL_API_KEY,
        )

        if "error" in result:
            return {"error": f"Term search failed: {result['error']}"}

        return result

    @mcp.tool()
    def get_branch_children(
        branch_iri: str,
        ontology_acronym: str,
    ) -> Dict[str, Any]:
        """
        Fetch all immediate children terms for a given branch in an ontology.

        Use this tool to retrieve the child terms under a specific branch IRI
        in a BioPortal ontology. This is useful for exploring the hierarchy of
        an ontology or populating dropdown options for a controlled vocabulary.

        Args:
            branch_iri: IRI of the branch to get children for
                       (e.g., "http://purl.obolibrary.org/obo/CHEBI_23367")
            ontology_acronym: Ontology acronym to search within
                             (e.g., "CHEBI", "HRAVS")

        Returns:
            BioPortal response containing child terms with their prefLabels
        """
        result = get_children_from_branch(
            branch_iri=branch_iri,
            ontology_acronym=ontology_acronym,
            bioportal_api_key=BIOPORTAL_API_KEY,
        )

        if "error" in result:
            return {"error": f"Get branch children failed: {result['error']}"}

        return result

    # Start the MCP server
    print("Starting CEDAR MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import argparse
import os
import sys
from typing import Any, Dict, List
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

from .processing import clean_template_response, clean_template_instance_response
from .external_api import search_instance_ids, get_instance


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
        print("Error: CEDAR API key not provided. Please set CEDAR_API_KEY environment variable or use --cedar-api-key.")
        sys.exit(1)

    BIOPORTAL_API_KEY = args.bioportal_api_key or os.getenv("BIOPORTAL_API_KEY")
    if not BIOPORTAL_API_KEY:
        print("Error: BioPortal API key not provided. Please set BIOPORTAL_API_KEY environment variable or use --bioportal-api-key.")
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
            "Authorization": f"apiKey {CEDAR_API_KEY}"
        }
        
        # Encode the template ID for URL
        encoded_template_id = quote(template_id, safe='')
        
        # Build the URL with a simple query parameter
        base_url = f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        
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
    def get_instances_based_on_template(template_id: str) -> List[Dict[str, Any]]:
        """
        Get all template instances based on a CEDAR template ID.
        
        This tool searches for all instances of a given template and fetches their complete content.
        
        Args:
            template_id: The template ID or full URL from CEDAR repository
                        (e.g., "https://repo.metadatacenter.org/templates/e019284e-48d1-4494-bc83-ddefd28dfbac")
        
        Returns:
            List of dictionaries containing the full JSON content of each template instance.
            Returns empty list if no instances found.
            Returns error dictionary if search or fetching fails.
        """
        # Step 1: Search for all instance IDs given a template ID
        search_result = search_instance_ids(template_id, CEDAR_API_KEY)
        
        # Check if search failed
        if "error" in search_result:
            return [{"error": f"Failed to search for template instances: {search_result['error']}"}]
        
        instance_ids = search_result.get("instance_ids", [])
        
        # If no instances found, return empty list
        if not instance_ids:
            return []
        
        # Step 2: Fetch content for each instance
        instances = []
        failed_instances = []
        
        for instance_id in instance_ids:
            instance_content = get_instance(instance_id, CEDAR_API_KEY)
            
            # Check if this instance fetch failed
            if "error" in instance_content:
                failed_instances.append({
                    "instance_id": instance_id,
                    "error": instance_content["error"]
                })
            else:
                # Clean the instance content before adding to results
                cleaned_instance = clean_template_instance_response(instance_content)
                instances.append(cleaned_instance)
        
        # Step 3: Return results with error summary if needed
        if failed_instances and not instances:
            # Complete failure: return error
            return [{
                "error": f"Failed to fetch any instance content. Found {len(instance_ids)} instance IDs but could not fetch any content.",
                "failure_details": failed_instances[:10]  # Show first 10 failures
            }]
        else:
            # Complete success: return all instances
            return instances

    # Start the MCP server
    print(f"Starting CEDAR MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
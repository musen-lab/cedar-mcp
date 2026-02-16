#!/usr/bin/env python3

from typing import Any, Dict, cast
from urllib.parse import quote
import requests


def get_children_from_branch(
    branch_iri: str, ontology_acronym: str, bioportal_api_key: str
) -> Dict[str, Any]:
    """
    Fetch children terms from BioPortal for a given branch URI.

    Args:
        branch_iri: IRI of the branch to get children for
        ontology_acronym: Ontology acronym (e.g., "HRAVS")
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing raw BioPortal API response or error information
    """
    try:
        # URL encode the branch IRI for safe inclusion in URL
        encoded_iri = quote(branch_iri, safe="")

        # Build the BioPortal API URL
        base_url = f"https://data.bioontology.org/ontologies/{ontology_acronym}/classes/{encoded_iri}/children"

        # Set query parameters as shown in cURL example
        params = {
            "display_context": "false",
            "display_links": "false",
            "include_views": "false",
            "pagesize": "999",
            "include": "prefLabel",
        }

        # Set authorization header
        headers = {"Authorization": f"apiKey token={bioportal_api_key}"}

        # Make the API request
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()

        # Return the raw JSON response from BioPortal
        return response.json()

    except requests.exceptions.RequestException as e:
        # Handle HTTP errors gracefully
        return {"error": f"Failed to fetch children from BioPortal: {str(e)}"}
    except (KeyError, ValueError) as e:
        # Handle JSON parsing errors
        return {"error": f"Failed to parse BioPortal response: {str(e)}"}


def search_terms(
    search_string: str,
    ontology_acronym: str,
    branch_iri: str,
    bioportal_api_key: str,
) -> Dict[str, Any]:
    """
    Search BioPortal for standardized ontology terms within a specific branch.

    Args:
        search_string: The term label or keyword to search for
        ontology_acronym: Ontology acronym (e.g., "CHEBI", "HRAVS")
        branch_iri: IRI of the branch to restrict the search to
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing raw BioPortal search response or error information
    """
    try:
        base_url = "https://data.bioontology.org/search"

        params = {
            "q": search_string,
            "ontology": ontology_acronym,
            "subtree_root_id": branch_iri,
            "include": "prefLabel,definition,synonym",
            "display_links": "false",
            "display_context": "false",
            "include_views": "false",
        }

        headers = {"Authorization": f"apiKey token={bioportal_api_key}"}

        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to search BioPortal: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse BioPortal search response: {str(e)}"}


def search_instance_ids(
    template_id: str, cedar_api_key: str, limit: int = 10, offset: int = 0
) -> Dict[str, Any]:
    """
    Search for template instances with pagination support.

    Args:
        template_id: Template ID (UUID or full URL)
        cedar_api_key: CEDAR API key for authentication
        limit: Number of instances to fetch
        offset: Starting position

    Returns:
        Dictionary containing:
        - instance_ids: List of instance IDs for this page
        - pagination: Pagination metadata
        - error: Error message if failed
    """
    try:
        # Convert template ID to full URL format if needed
        if not template_id.startswith("https://"):
            template_url = f"https://repo.metadatacenter.org/templates/{template_id}"
        else:
            template_url = template_id

        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        # Build the search API URL
        base_url = "https://resource.metadatacenter.org/search"
        params = {
            "version": "latest",
            "limit": limit,
            "is_based_on": template_url,
            "offset": offset,
        }

        # Make the API request
        response = requests.get(
            base_url, headers=headers, params=cast(Any, params), timeout=30
        )
        response.raise_for_status()
        search_data = response.json()

        # Extract information
        total_count = search_data.get("totalCount", 0)
        resources = search_data.get("resources", [])

        # Extract instance IDs from current page
        instance_ids = []
        for resource in resources:
            instance_id = resource.get("@id")
            if instance_id:
                instance_ids.append(instance_id)

        # Calculate pagination metadata
        current_page = (offset // limit) + 1
        total_pages = (
            (total_count + limit - 1) // limit if limit > 0 else 0
        )  # Ceiling division
        has_next = offset + limit < total_count

        pagination_metadata = {
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "current_page": current_page,
            "total_pages": total_pages,
            "has_next": has_next,
        }

        return {"instance_ids": instance_ids, "pagination": pagination_metadata}

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to search CEDAR instances: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse CEDAR search response: {str(e)}"}


def get_instance(instance_id: str, cedar_api_key: str) -> Dict[str, Any]:
    """
    Fetch the full content of a CEDAR template instance.

    Args:
        instance_id: Full instance URL (e.g., "https://repo.metadatacenter.org/template-instances/{uuid}")
        cedar_api_key: CEDAR API key for authentication

    Returns:
        Dictionary containing instance content or error information
    """
    try:
        # URL encode the instance ID for safe inclusion in URL
        encoded_instance_id = quote(instance_id, safe="")

        # Build the instance API URL
        base_url = f"https://resource.metadatacenter.org/template-instances/{encoded_instance_id}"

        # Set authorization header
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        # Make the API request with timeout
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Return the raw JSON response from CEDAR
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch CEDAR instance content: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse CEDAR instance response: {str(e)}"}

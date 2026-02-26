#!/usr/bin/env python3

import asyncio
import logging
import time
from typing import Any, Dict, Optional, cast
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


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

        # Make the API request with retry on 429
        response = _request_with_retry(base_url, headers=headers, params=params)
        response.raise_for_status()

        # Return the raw JSON response from BioPortal
        return response.json()

    except requests.exceptions.RequestException as e:
        # Handle HTTP errors gracefully
        return {"error": f"Failed to fetch children from BioPortal: {str(e)}"}
    except (KeyError, ValueError) as e:
        # Handle JSON parsing errors
        return {"error": f"Failed to parse BioPortal response: {str(e)}"}


async def async_get_children_from_branch(
    branch_iri: str, ontology_acronym: str, bioportal_api_key: str
) -> Dict[str, Any]:
    """
    Async wrapper around get_children_from_branch.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        branch_iri: IRI of the branch to get children for
        ontology_acronym: Ontology acronym (e.g., "HRAVS")
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing raw BioPortal API response or error information
    """
    return await asyncio.to_thread(
        get_children_from_branch, branch_iri, ontology_acronym, bioportal_api_key
    )


def search_terms_from_branch(
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

        response = _request_with_retry(base_url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to search BioPortal: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse BioPortal search response: {str(e)}"}


async def async_search_terms_from_branch(
    search_string: str,
    ontology_acronym: str,
    branch_iri: str,
    bioportal_api_key: str,
) -> Dict[str, Any]:
    """
    Async wrapper around search_terms_from_branch.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        search_string: The term label or keyword to search for
        ontology_acronym: Ontology acronym (e.g., "CHEBI", "HRAVS")
        branch_iri: IRI of the branch to restrict the search to
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing raw BioPortal search response or error information
    """
    return await asyncio.to_thread(
        search_terms_from_branch,
        search_string,
        ontology_acronym,
        branch_iri,
        bioportal_api_key,
    )


def search_terms_from_ontology(
    search_string: str,
    ontology_acronym: str,
    bioportal_api_key: str,
) -> Dict[str, Any]:
    """
    Search BioPortal for standardized ontology terms within an entire ontology.

    Args:
        search_string: The term label or keyword to search for
        ontology_acronym: Ontology acronym (e.g., "NCIT", "CHEBI")
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing raw BioPortal search response or error information
    """
    try:
        base_url = "https://data.bioontology.org/search"

        params = {
            "q": search_string,
            "ontologies": ontology_acronym,
            "include": "prefLabel,definition,synonym",
            "display_links": "false",
            "display_context": "false",
            "include_views": "false",
        }

        headers = {"Authorization": f"apiKey token={bioportal_api_key}"}

        response = _request_with_retry(base_url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to search BioPortal: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse BioPortal search response: {str(e)}"}


async def async_search_terms_from_ontology(
    search_string: str,
    ontology_acronym: str,
    bioportal_api_key: str,
) -> Dict[str, Any]:
    """
    Async wrapper around search_terms_from_ontology.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        search_string: The term label or keyword to search for
        ontology_acronym: Ontology acronym (e.g., "NCIT", "CHEBI")
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing raw BioPortal search response or error information
    """
    return await asyncio.to_thread(
        search_terms_from_ontology,
        search_string,
        ontology_acronym,
        bioportal_api_key,
    )


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

        # Make the API request with retry on 429
        response = _request_with_retry(
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


async def async_search_instance_ids(
    template_id: str,
    cedar_api_key: str,
    limit: int = 10,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Async wrapper around search_instance_ids.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        template_id: Template ID (UUID or full URL)
        cedar_api_key: CEDAR API key for authentication
        limit: Number of instances to fetch
        offset: Starting position

    Returns:
        Dictionary containing instance_ids, pagination, or error
    """
    return await asyncio.to_thread(
        search_instance_ids, template_id, cedar_api_key, limit, offset
    )


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

        # Make the API request with retry on 429
        response = _request_with_retry(base_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Return the raw JSON response from CEDAR
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch CEDAR instance content: {str(e)}"}
    except (KeyError, ValueError) as e:
        return {"error": f"Failed to parse CEDAR instance response: {str(e)}"}


async def async_get_instance(instance_id: str, cedar_api_key: str) -> Dict[str, Any]:
    """
    Async wrapper around get_instance.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        instance_id: Full instance URL
        cedar_api_key: CEDAR API key for authentication

    Returns:
        Dictionary containing instance content or error information
    """
    return await asyncio.to_thread(get_instance, instance_id, cedar_api_key)


def get_class_tree(
    class_iri: str, ontology_acronym: str, bioportal_api_key: str
) -> Dict[str, Any]:
    """
    Fetch the hierarchical tree structure for a given ontology class from BioPortal.

    Args:
        class_iri: IRI of the class to get the tree for
                  (e.g., "http://purl.obolibrary.org/obo/MONDO_0005180")
        ontology_acronym: Ontology acronym (e.g., "MONDO", "CHEBI")
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing the tree nodes list under the "tree" key,
        or error information
    """
    try:
        # URL encode the class IRI for safe inclusion in URL
        encoded_iri = quote(class_iri, safe="")

        # Build the BioPortal API URL
        base_url = f"https://data.bioontology.org/ontologies/{ontology_acronym}/classes/{encoded_iri}/tree"

        # Set query parameters
        params = {
            "display_links": "false",
            "display_context": "false",
            "include_views": "false",
        }

        # Set authorization header
        headers = {"Authorization": f"apiKey token={bioportal_api_key}"}

        # Make the API request with retry on 429
        response = _request_with_retry(base_url, headers=headers, params=params)
        response.raise_for_status()

        # Wrap the list response in a dict for cache compatibility
        return {"tree": response.json()}

    except requests.exceptions.RequestException as e:
        # Handle HTTP errors gracefully
        return {"error": f"Failed to fetch class tree from BioPortal: {str(e)}"}
    except (KeyError, ValueError) as e:
        # Handle JSON parsing errors
        return {"error": f"Failed to parse BioPortal response: {str(e)}"}


async def async_get_class_tree(
    class_iri: str,
    ontology_acronym: str,
    bioportal_api_key: str,
) -> Dict[str, Any]:
    """
    Async wrapper around get_class_tree.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        class_iri: IRI of the class to get the tree for
        ontology_acronym: Ontology acronym (e.g., "MONDO", "CHEBI")
        bioportal_api_key: BioPortal API key for authentication

    Returns:
        Dictionary containing the tree nodes list or error information
    """
    return await asyncio.to_thread(
        get_class_tree, class_iri, ontology_acronym, bioportal_api_key
    )


def get_template(template_id: str, cedar_api_key: str) -> Dict[str, Any]:
    """
    Fetch a template from the CEDAR repository.

    Args:
        template_id: The template ID or full URL from CEDAR repository
                    (e.g., "https://repo.metadatacenter.org/templates/...")
        cedar_api_key: CEDAR API key for authentication

    Returns:
        Dictionary containing raw CEDAR template data or error information
    """
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": f"apiKey {cedar_api_key}",
        }

        # Encode the template ID for URL
        encoded_template_id = quote(template_id, safe="")

        # Build the URL
        base_url = (
            f"https://resource.metadatacenter.org/templates/{encoded_template_id}"
        )

        response = _request_with_retry(base_url, headers=headers)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch CEDAR template: {str(e)}"}


async def async_get_template(template_id: str, cedar_api_key: str) -> Dict[str, Any]:
    """
    Async wrapper around get_template.

    Delegates to the sync implementation via asyncio.to_thread so the
    event loop is not blocked during the HTTP call.

    Args:
        template_id: The template ID or full URL from CEDAR repository
        cedar_api_key: CEDAR API key for authentication

    Returns:
        Dictionary containing raw CEDAR template data or error information
    """
    return await asyncio.to_thread(get_template, template_id, cedar_api_key)


def _request_with_retry(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
) -> requests.Response:
    """
    Make an HTTP GET request with retry logic for HTTP 429 (Too Many Requests).

    Uses exponential backoff, respecting the Retry-After header when present.

    Args:
        url: The URL to request
        headers: HTTP headers to include
        params: Optional query parameters
        timeout: Optional request timeout in seconds
        max_retries: Maximum number of retries on 429 responses
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries

    Returns:
        The successful HTTP response

    Raises:
        requests.exceptions.HTTPError: If all retries are exhausted or a non-429 error occurs
    """
    for attempt in range(max_retries + 1):
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        if response.status_code != 429:
            return response

        if attempt == max_retries:
            # All retries exhausted — raise as HTTP error
            response.raise_for_status()

        # Determine wait time from Retry-After header or exponential backoff
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = initial_delay * (2**attempt)
        else:
            delay = initial_delay * (2**attempt)

        # Cap the delay to avoid excessively long waits
        delay = min(delay, max_delay)

        logger.info(
            "Received 429 from %s, retrying in %.1fs (attempt %d/%d)",
            url,
            delay,
            attempt + 1,
            max_retries,
        )
        time.sleep(delay)

    # Should not reach here, but satisfy type checker
    return response

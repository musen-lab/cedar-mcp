#!/usr/bin/env python3

from typing import Any, Dict
from urllib.parse import quote
import requests

def get_children_from_branch(branch_iri: str, ontology_acronym: str, bioportal_api_key: str) -> Dict[str, Any]:
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
        encoded_iri = quote(branch_iri, safe='')
        
        # Build the BioPortal API URL
        base_url = f"https://data.bioontology.org/ontologies/{ontology_acronym}/classes/{encoded_iri}/children"
        
        # Set query parameters as shown in cURL example
        params = {
            'display_context': 'false',
            'display_links': 'false', 
            'include_views': 'false',
            'pagesize': '999',
            'include': 'prefLabel'
        }
        
        # Set authorization header
        headers = {
            'Authorization': f'apiKey token={bioportal_api_key}'
        }
        
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


def search_instance_ids(template_id: str, cedar_api_key: str, limit_per_call: int = 100) -> Dict[str, Any]:
    """
    Search for template instances based on a template ID.
    
    Args:
        template_id: Template ID (UUID or full URL)
        cedar_api_key: CEDAR API key for authentication
        limit_per_call: Number of instances to fetch per API call (default: 100)
        
    Returns:
        Dictionary containing all instance IDs or error information
        Format: {"instance_ids": [list of @id values], "total_count": int} or {"error": str}
    """
    try:
        # Convert template ID to full URL format if needed
        if not template_id.startswith("https://"):
            template_url = f"https://repo.metadatacenter.org/templates/{template_id}"
        else:
            template_url = template_id
        
        # Set authorization header
        headers = {
            'Accept': 'application/json',
            'Authorization': f'apiKey {cedar_api_key}'
        }
        
        # Start with first page
        all_instance_ids = []
        offset = 0
        total_count = 0
        
        while True:
            # Build the search API URL
            base_url = "https://resource.metadatacenter.org/search"
            params = {
                'version': 'latest',
                'limit': limit_per_call,
                'is_based_on': template_url,
                'offset': offset
            }
            
            # Make the API request with timeout
            response = requests.get(base_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            search_data = response.json()
            
            # Extract total count from first response
            if offset == 0:
                total_count = search_data.get('totalCount', 0)
                
                # If no instances found, return empty result
                if total_count == 0:
                    return {"instance_ids": [], "total_count": 0}
            
            # Extract instance IDs from current page
            resources = search_data.get('resources', [])
            for resource in resources:
                instance_id = resource.get('@id')
                if instance_id:
                    all_instance_ids.append(instance_id)
            
            # Check if there's a next page
            paging = search_data.get('paging', {})
            next_page = paging.get('next')
            
            # If no next page, we're done
            if not next_page:
                break
            
            # Move to next page
            offset += limit_per_call
            
            # Safety check to prevent infinite loops
            if len(all_instance_ids) >= total_count:
                break
        
        return {
            "instance_ids": all_instance_ids,
            "total_count": total_count
        }
        
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
        encoded_instance_id = quote(instance_id, safe='')
        
        # Build the instance API URL
        base_url = f"https://resource.metadatacenter.org/template-instances/{encoded_instance_id}"
        
        # Set authorization header
        headers = {
            'Accept': 'application/json',
            'Authorization': f'apiKey {cedar_api_key}'
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

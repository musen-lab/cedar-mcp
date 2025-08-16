#!/usr/bin/env python3

import os
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

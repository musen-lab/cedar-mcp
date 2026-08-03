#!/usr/bin/env python3

"""
Cleaning and transformation of CEDAR responses.

Templates are handled in CEDAR's YAML rendering only, since it carries far
fewer tokens than the JSON-LD form:

- template_yaml: templates in YAML format
- branch_expansion: listing the terms allowed by an ontology branch
- instance: template instances in JSON-LD format

Cleaning and branch expansion are independent transforms over the same
dictionary shape, so they can be applied in either order, or on their own.
"""

from .branch_expansion import expand_template_branches
from .instance import clean_template_instance_response
from .template_yaml import clean_template_yaml_response

__all__ = [
    "clean_template_instance_response",
    "clean_template_yaml_response",
    "expand_template_branches",
]

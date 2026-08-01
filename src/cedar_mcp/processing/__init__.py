#!/usr/bin/env python3

"""
Cleaning and transformation of CEDAR responses.

Each format CEDAR can return has its own module:

- template_json: templates in JSON-LD format
- template_yaml: templates in YAML format
- instance: template instances in JSON-LD format

Both template cleaners produce the same simplified output, so callers do not
care which format the template arrived in.
"""

from .instance import clean_template_instance_response
from .template_json import clean_template_response
from .template_yaml import clean_template_yaml_response

__all__ = [
    "clean_template_instance_response",
    "clean_template_response",
    "clean_template_yaml_response",
]

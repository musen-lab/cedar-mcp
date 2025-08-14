#!/usr/bin/env python3

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ControlledTermValue(BaseModel):
    """
    Represents a single value in a controlled term field.
    """
    label: str = Field(..., description="Human-readable label")
    iri: Optional[str] = Field(None, description="IRI/URI identifier (omitted for literals)")


class ControlledTermDefault(BaseModel):
    """
    Represents the default value for a controlled term field.
    """
    label: str = Field(..., description="Default label")
    iri: str = Field(..., description="Default IRI/URI")


class FieldConfiguration(BaseModel):
    """
    Configuration settings for a field.
    """
    required: bool = Field(False, description="Whether the field is required")


class FieldDefinition(BaseModel):
    """
    Represents a field in the output template.
    """
    name: str = Field(..., description="Field name")
    description: str = Field(..., description="Field description")
    prefLabel: str = Field(..., description="Human-readable label")
    datatype: str = Field(..., description="Data type (string, integer, decimal, boolean)")
    configuration: FieldConfiguration = Field(..., description="Field configuration")
    regex: Optional[str] = Field(None, description="Validation regex pattern")
    default: Optional[Union[ControlledTermDefault, str, int, float, bool]] = Field(None, description="Default value")
    values: Optional[List[ControlledTermValue]] = Field(None, description="Controlled term values")


class SimplifiedTemplate(BaseModel):
    """
    Represents the complete simplified template structure.
    """
    type: str = Field("template", description="Template type")
    name: str = Field(..., description="Template name")
    children: List[FieldDefinition] = Field(..., description="Template fields")
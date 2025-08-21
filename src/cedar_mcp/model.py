#!/usr/bin/env python3

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ControlledTermValue(BaseModel):
    """
    Represents a single value in a controlled term field.
    """

    label: str = Field(..., description="Human-readable label")
    iri: Optional[str] = Field(
        None, description="IRI/URI identifier (omitted for literals)"
    )


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
    datatype: str = Field(
        ..., description="Data type (string, integer, decimal, boolean)"
    )
    configuration: FieldConfiguration = Field(..., description="Field configuration")
    regex: Optional[str] = Field(None, description="Validation regex pattern")
    default: Optional[Union[ControlledTermDefault, str, int, float, bool]] = Field(
        None, description="Default value"
    )
    values: Optional[List[ControlledTermValue]] = Field(
        None, description="Controlled term values"
    )


class ElementDefinition(BaseModel):
    """
    Represents a template element that can contain nested fields or other elements.
    """

    name: str = Field(..., description="Element name")
    description: str = Field(..., description="Element description")
    prefLabel: str = Field(..., description="Human-readable label")
    datatype: str = Field(
        "element", description="Data type (always 'element' for TemplateElements)"
    )
    configuration: FieldConfiguration = Field(..., description="Element configuration")
    is_array: bool = Field(False, description="Whether this element represents an array")
    children: List[Union["FieldDefinition", "ElementDefinition"]] = Field(
        default_factory=list, description="Nested fields and elements"
    )


class SimplifiedTemplate(BaseModel):
    """
    Represents the complete simplified template structure.
    """

    type: str = Field("template", description="Template type")
    name: str = Field(..., description="Template name")
    children: List[Union[FieldDefinition, ElementDefinition]] = Field(
        ..., description="Template fields and elements"
    )


# Update forward references for self-referencing models
ElementDefinition.model_rebuild()

#!/usr/bin/env python3

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ClassOption(BaseModel):
    """
    Represents a single class option with a label and term IRI.
    """

    label: str = Field(..., description="Human-readable label")
    term_iri: str = Field(..., description="IRI/URI identifier for the class")


class LiteralConstraint(BaseModel):
    """
    Constraint for literal (plain text) value options.
    """

    type: Literal["literal"] = "literal"
    options: List[str] = Field(..., description="List of allowed literal labels")


class OntologyConstraint(BaseModel):
    """
    Constraint indicating values should come from one or more ontologies.
    """

    type: Literal["ontology"] = "ontology"
    ontology_acronyms: List[str] = Field(
        ..., description="List of ontology acronyms to search"
    )


class ClassConstraint(BaseModel):
    """
    Constraint for specific class options with labels and IRIs.
    """

    type: Literal["class"] = "class"
    options: List[ClassOption] = Field(..., description="List of class options")


class BranchConstraint(BaseModel):
    """
    Constraint indicating values should come from a specific ontology branch.
    """

    type: Literal["branch"] = "branch"
    ontology_acronym: str = Field(..., description="Ontology acronym")
    branch_iri: str = Field(..., description="IRI of the branch root")


ValueConstraint = Union[
    LiteralConstraint, OntologyConstraint, ClassConstraint, BranchConstraint
]


class ControlledTermDefault(BaseModel):
    """
    Represents the default value for a controlled term field.
    """

    label: str = Field(..., description="Default label")
    iri: str = Field(..., description="Default IRI/URI")



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
    required: bool = Field(False, description="Whether the field is required")
    is_array: bool = Field(False, description="Whether this field represents an array")
    regex: Optional[str] = Field(None, description="Validation regex pattern")
    default: Optional[Union[ControlledTermDefault, str, int, float, bool]] = Field(
        None, description="Default value"
    )
    values: Optional[List[ValueConstraint]] = Field(
        None, description="Value constraints for controlled term fields"
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
    required: bool = Field(False, description="Whether the element is required")
    is_array: bool = Field(
        False, description="Whether this element represents an array"
    )
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

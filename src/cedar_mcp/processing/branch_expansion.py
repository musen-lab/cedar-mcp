#!/usr/bin/env python3

"""Expansion of ontology branch constraints into their child term labels."""

import logging
from typing import Callable, List, Sequence, Union

from ..model import BranchConstraint, ElementDefinition, FieldDefinition

logger = logging.getLogger(__name__)

# Given a branch IRI and its ontology acronym, return the labels of the terms
# directly under that branch root.
BranchOptionFetcher = Callable[[str, str], List[str]]


def expand_branch_constraints(
    children: Sequence[Union[FieldDefinition, ElementDefinition]],
    fetch_branch_options: BranchOptionFetcher,
) -> None:
    """
    Fill in the child term labels for every branch constraint in a template.

    On its own a branch constraint only says which ontology subtree a value has
    to come from; the root itself is a category, not a value. Expanding it lists
    the terms directly under that root so a consumer can pick one without
    querying BioPortal.

    Each branch costs one lookup, so this is only worth doing on request. A
    branch whose lookup fails, or that has no children, is left unexpanded
    rather than failing the whole template.

    Args:
        children: Field and element definitions to walk, modified in place
        fetch_branch_options: Callable returning the child labels for a branch
    """
    for child in children:
        if isinstance(child, ElementDefinition):
            expand_branch_constraints(child.children, fetch_branch_options)
            continue

        for constraint in child.permissible_values or []:
            if not isinstance(constraint, BranchConstraint):
                continue

            try:
                options = fetch_branch_options(
                    constraint.branch_iri, constraint.ontology_acronym
                )
            except Exception as e:
                logger.warning(
                    "Could not expand branch %s from %s: %s",
                    constraint.branch_iri,
                    constraint.ontology_acronym,
                    e,
                )
                continue

            if options:
                constraint.options = options

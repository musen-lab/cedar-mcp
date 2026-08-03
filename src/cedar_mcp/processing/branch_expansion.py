#!/usr/bin/env python3

"""Expansion of ontology branch constraints into their child terms."""

import logging
from typing import Callable, List, Literal, Sequence, Union

from ..model import BranchConstraint, ClassOption, ElementDefinition, FieldDefinition

logger = logging.getLogger(__name__)

# How much of each branch to report:
#   "none"   - leave branches as a reference to their subtree
#   "labels" - list the child term labels
#   "terms"  - list the child terms as label and IRI pairs
BranchExpansion = Literal["none", "labels", "terms"]

# Given a branch IRI and its ontology acronym, return the terms directly under
# that branch root. Always the full label and IRI form; callers narrow it down.
BranchOptionFetcher = Callable[[str, str], List[ClassOption]]


def expand_branch_constraints(
    children: Sequence[Union[FieldDefinition, ElementDefinition]],
    fetch_branch_options: BranchOptionFetcher,
    mode: BranchExpansion = "labels",
) -> None:
    """
    List the child terms of every branch constraint in a template.

    On its own a branch constraint only says which ontology subtree a value has
    to come from; the root itself is a category, not a value. Expanding it lists
    the terms directly under that root so a consumer can pick one without
    querying BioPortal.

    Once expanded, the branch root is no longer worth reporting, so
    `ontology_acronym` and `branch_iri` are dropped in favour of the options.
    Note that `"labels"` therefore leaves no IRI at all: it suits reading a
    template, while `"terms"` suits filling one in.

    Each branch costs one lookup, so this is only worth doing on request. A
    branch whose lookup fails, or that has no children, keeps its root so it
    stays resolvable, rather than failing the whole template.

    Args:
        children: Field and element definitions to walk, modified in place
        fetch_branch_options: Callable returning the child terms for a branch
        mode: Whether to list nothing, labels only, or labels with their IRIs
    """
    if mode == "none":
        return

    for child in children:
        if isinstance(child, ElementDefinition):
            expand_branch_constraints(child.children, fetch_branch_options, mode)
            continue

        for constraint in child.permissible_values or []:
            if not isinstance(constraint, BranchConstraint):
                continue

            # No root to look up: already expanded, so leave it alone
            if constraint.branch_iri is None or constraint.ontology_acronym is None:
                continue

            try:
                terms = fetch_branch_options(
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

            if not terms:
                continue

            constraint.options = (
                list(terms) if mode == "terms" else [term.label for term in terms]
            )
            # The root only existed so the subtree could be looked up
            constraint.ontology_acronym = None
            constraint.branch_iri = None

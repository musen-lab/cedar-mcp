#!/usr/bin/env python3

"""Expansion of ontology branch constraints into their child terms."""

import copy
import logging
from typing import Any, Callable, Dict, List, Literal, Optional

from ..model import ClassOption

logger = logging.getLogger(__name__)

# How much of each branch to report:
#   "none"   - leave branches as a reference to their subtree
#   "labels" - list the child term labels
#   "terms"  - list the child terms as label and IRI pairs
BranchExpansion = Literal["none", "labels", "terms"]

# Given a branch IRI and its ontology acronym, return the terms directly under
# that branch root. Always the full label and IRI form; the mode narrows it down.
BranchOptionFetcher = Callable[[str, str], List[ClassOption]]

# Where branch constraints live. A CEDAR template keeps them under `values`; a
# template that has been through clean_template_response keeps them under
# `permissible_values`. Accepting both is what lets cleaning and expansion run
# in either order.
_CONSTRAINT_KEYS = ("values", "permissible_values")

# The branch root, as CEDAR spells it and as the cleaner renames it.
_IRI_KEYS = ("iri", "branch_iri")
_ACRONYM_KEYS = ("acronym", "ontology_acronym")
_CLEANED_ROOT_KEYS = ("branch_iri", "ontology_acronym")


def expand_template_branches(
    template: Dict[str, Any],
    mode: BranchExpansion = "labels",
    fetch_branch_options: Optional[BranchOptionFetcher] = None,
) -> Dict[str, Any]:
    """
    List the terms allowed by every ontology branch in a template.

    On its own a branch constraint only says which ontology subtree a value has
    to come from; the root itself is a category, not a value. Expanding it lists
    the terms directly under that root so a consumer can pick one without
    querying BioPortal.

    Accepts a template as CEDAR returned it or one already cleaned by
    clean_template_response, and returns the same kind it was given. The
    two transforms are therefore order independent: expanding a cleaned template
    and cleaning an expanded one produce the same result.

    Each branch costs one lookup, so this is only worth doing on request. A
    branch whose lookup fails, or that has no children, keeps its root so it
    stays resolvable, rather than failing the whole template.

    Args:
        template: Template dictionary, either as CEDAR returned it or cleaned
        mode: Whether to list nothing, labels only, or labels with their IRIs
        fetch_branch_options: Callable returning the child terms for a branch,
                             required for expansion to happen

    Returns:
        A new template dictionary; the input is left untouched
    """
    if mode == "none" or fetch_branch_options is None:
        return template

    expanded = copy.deepcopy(template)

    def expand(constraint: Dict[str, Any]) -> None:
        _expand_constraint(constraint, mode, fetch_branch_options)

    walk_branch_constraints(expanded, expand)
    normalize_expanded_branches(expanded)
    return expanded


def walk_branch_constraints(
    template: Dict[str, Any],
    visit: Callable[[Dict[str, Any]], None],
) -> None:
    """
    Apply a function to every branch constraint in a template.

    Both template shapes nest through `children` and tag branch constraints with
    `type: "branch"`, so one traversal serves them both.

    Args:
        template: Template or element dictionary to walk
        visit: Called with each branch constraint, free to modify it in place
    """
    children = template.get("children")
    if not isinstance(children, list):
        return

    for child in children:
        if not isinstance(child, dict):
            continue

        for key in _CONSTRAINT_KEYS:
            constraints = child.get(key)
            if not isinstance(constraints, list):
                continue
            for constraint in constraints:
                if isinstance(constraint, dict) and constraint.get("type") == "branch":
                    visit(constraint)

        walk_branch_constraints(child, visit)


def normalize_expanded_branches(template: Dict[str, Any]) -> None:
    """
    Drop the branch root from every constraint whose terms are listed.

    Listing the terms is the whole point of expanding, so repeating the root
    beside them adds nothing. Only the cleaned spelling is removed: a raw CEDAR
    template keeps its own keys so it stays a usable CEDAR artifact.

    Both cleaning and expansion end with this, which is what makes the two
    orders agree.

    Args:
        template: Template dictionary to normalise in place
    """

    def drop_root(constraint: Dict[str, Any]) -> None:
        if constraint.get("options"):
            for key in _CLEANED_ROOT_KEYS:
                constraint.pop(key, None)

    walk_branch_constraints(template, drop_root)


def _expand_constraint(
    constraint: Dict[str, Any],
    mode: BranchExpansion,
    fetch_branch_options: BranchOptionFetcher,
) -> None:
    """
    Fill in the allowed terms for a single branch constraint.

    Args:
        constraint: A branch constraint, modified in place
        mode: Whether to list labels only or labels with their IRIs
        fetch_branch_options: Callable returning the child terms for a branch
    """
    # Already expanded, so leave it alone and keep this idempotent
    if "options" in constraint:
        return

    branch_iri = _first_value(constraint, _IRI_KEYS)
    ontology_acronym = _first_value(constraint, _ACRONYM_KEYS)
    if branch_iri is None or ontology_acronym is None:
        return

    try:
        terms = fetch_branch_options(branch_iri, ontology_acronym)
    except Exception as e:
        logger.warning(
            "Could not expand branch %s from %s: %s",
            branch_iri,
            ontology_acronym,
            e,
        )
        return

    if not terms:
        return

    if mode == "terms":
        constraint["options"] = [term.model_dump() for term in terms]
    else:
        constraint["options"] = [term.label for term in terms]


def _first_value(constraint: Dict[str, Any], keys: tuple) -> Optional[str]:
    """
    Return the first present, non-empty string among the given keys.

    Args:
        constraint: Constraint dictionary to read
        keys: Candidate key names, in preference order

    Returns:
        The value found, or None
    """
    for key in keys:
        value = constraint.get(key)
        if isinstance(value, str) and value:
            return value
    return None

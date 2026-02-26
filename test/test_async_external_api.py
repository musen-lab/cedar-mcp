#!/usr/bin/env python3

"""
Unit tests for async wrapper functions in external_api.py.

Each test verifies that the async wrapper correctly delegates to
its sync counterpart via asyncio.to_thread.
"""

import asyncio
from unittest.mock import patch

import pytest

from src.cedar_mcp.external_api import (
    async_get_children_from_branch,
    async_get_class_tree,
    async_get_instance,
    async_get_template,
    async_search_instance_ids,
    async_search_terms_from_branch,
    async_search_terms_from_ontology,
)


@pytest.mark.unit
class TestAsyncGetChildrenFromBranch:
    """Tests for async_get_children_from_branch."""

    def test_delegates_to_sync(self) -> None:
        """Async wrapper should call get_children_from_branch with the same args."""
        expected = {"collection": [{"prefLabel": "child1"}]}
        with patch(
            "src.cedar_mcp.external_api.get_children_from_branch",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(
                async_get_children_from_branch("iri", "ONTO", "key123")
            )
        mock_sync.assert_called_once_with("iri", "ONTO", "key123")
        assert result == expected


@pytest.mark.unit
class TestAsyncSearchTermsFromBranch:
    """Tests for async_search_terms_from_branch."""

    def test_delegates_to_sync(self) -> None:
        """Async wrapper should call search_terms_from_branch with the same args."""
        expected = {"collection": [{"prefLabel": "aspirin"}]}
        with patch(
            "src.cedar_mcp.external_api.search_terms_from_branch",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(
                async_search_terms_from_branch("aspirin", "CHEBI", "iri", "key123")
            )
        mock_sync.assert_called_once_with("aspirin", "CHEBI", "iri", "key123")
        assert result == expected


@pytest.mark.unit
class TestAsyncSearchTermsFromOntology:
    """Tests for async_search_terms_from_ontology."""

    def test_delegates_to_sync(self) -> None:
        """Async wrapper should call search_terms_from_ontology with the same args."""
        expected = {"collection": [{"prefLabel": "melanoma"}]}
        with patch(
            "src.cedar_mcp.external_api.search_terms_from_ontology",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(
                async_search_terms_from_ontology("melanoma", "NCIT", "key123")
            )
        mock_sync.assert_called_once_with("melanoma", "NCIT", "key123")
        assert result == expected


@pytest.mark.unit
class TestAsyncSearchInstanceIds:
    """Tests for async_search_instance_ids."""

    def test_delegates_to_sync_with_defaults(self) -> None:
        """Async wrapper should call search_instance_ids with default limit/offset."""
        expected = {"instance_ids": ["id1"], "pagination": {}}
        with patch(
            "src.cedar_mcp.external_api.search_instance_ids",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(async_search_instance_ids("tmpl_id", "key123"))
        mock_sync.assert_called_once_with("tmpl_id", "key123", 10, 0)
        assert result == expected

    def test_delegates_to_sync_with_custom_pagination(self) -> None:
        """Async wrapper should forward custom limit and offset."""
        expected = {"instance_ids": ["id2"], "pagination": {}}
        with patch(
            "src.cedar_mcp.external_api.search_instance_ids",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(
                async_search_instance_ids("tmpl_id", "key123", limit=5, offset=10)
            )
        mock_sync.assert_called_once_with("tmpl_id", "key123", 5, 10)
        assert result == expected


@pytest.mark.unit
class TestAsyncGetInstance:
    """Tests for async_get_instance."""

    def test_delegates_to_sync(self) -> None:
        """Async wrapper should call get_instance with the same args."""
        expected = {"schema:name": "Test Instance"}
        with patch(
            "src.cedar_mcp.external_api.get_instance",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(async_get_instance("inst_id", "key123"))
        mock_sync.assert_called_once_with("inst_id", "key123")
        assert result == expected


@pytest.mark.unit
class TestAsyncGetClassTree:
    """Tests for async_get_class_tree."""

    def test_delegates_to_sync(self) -> None:
        """Async wrapper should call get_class_tree with the same args."""
        expected = {"tree": [{"prefLabel": "root"}]}
        with patch(
            "src.cedar_mcp.external_api.get_class_tree",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(async_get_class_tree("class_iri", "MONDO", "key123"))
        mock_sync.assert_called_once_with("class_iri", "MONDO", "key123")
        assert result == expected


@pytest.mark.unit
class TestAsyncGetTemplate:
    """Tests for async_get_template."""

    def test_delegates_to_sync(self) -> None:
        """Async wrapper should call get_template with the same args."""
        expected = {"@id": "tmpl_id", "schema:name": "Test"}
        with patch(
            "src.cedar_mcp.external_api.get_template",
            return_value=expected,
        ) as mock_sync:
            result = asyncio.run(async_get_template("tmpl_id", "key123"))
        mock_sync.assert_called_once_with("tmpl_id", "key123")
        assert result == expected

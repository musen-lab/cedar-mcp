#!/usr/bin/env python3

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.cedar_mcp.external_api import _request_with_retry


@pytest.mark.unit
class TestRequestWithRetry:
    """Unit tests for the _request_with_retry helper."""

    def test_success_on_first_try(self):
        """Should return the response immediately when status is not 429."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.cedar_mcp.external_api.requests.get", return_value=mock_response) as mock_get:
            result = _request_with_retry(
                "https://example.com", headers={"Authorization": "test"}
            )

        assert result is mock_response
        assert mock_get.call_count == 1

    @patch("src.cedar_mcp.external_api.time.sleep")
    def test_retries_on_429_then_succeeds(self, mock_sleep: MagicMock):
        """Should retry on 429 and return the successful response."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {}

        mock_200 = MagicMock()
        mock_200.status_code = 200

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            side_effect=[mock_429, mock_200],
        ) as mock_get:
            result = _request_with_retry(
                "https://example.com",
                headers={"Authorization": "test"},
                initial_delay=0.1,
            )

        assert result is mock_200
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(0.1)

    @patch("src.cedar_mcp.external_api.time.sleep")
    def test_respects_retry_after_header(self, mock_sleep: MagicMock):
        """Should use the Retry-After header value as the delay."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "5"}

        mock_200 = MagicMock()
        mock_200.status_code = 200

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            side_effect=[mock_429, mock_200],
        ):
            result = _request_with_retry(
                "https://example.com",
                headers={"Authorization": "test"},
                initial_delay=1.0,
            )

        assert result is mock_200
        mock_sleep.assert_called_once_with(5.0)

    @patch("src.cedar_mcp.external_api.time.sleep")
    def test_raises_after_max_retries_exhausted(self, mock_sleep: MagicMock):
        """Should raise HTTPError after all retries are exhausted."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {}
        mock_429.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Too Many Requests"
        )

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            return_value=mock_429,
        ):
            with pytest.raises(requests.exceptions.HTTPError, match="429"):
                _request_with_retry(
                    "https://example.com",
                    headers={"Authorization": "test"},
                    max_retries=2,
                    initial_delay=0.01,
                )

        # Should have been called 3 times total (initial + 2 retries)
        assert mock_sleep.call_count == 2

    def test_does_not_retry_on_other_http_errors(self):
        """Should NOT retry on non-429 errors like 404 or 500."""
        mock_404 = MagicMock()
        mock_404.status_code = 404

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            return_value=mock_404,
        ) as mock_get:
            result = _request_with_retry(
                "https://example.com", headers={"Authorization": "test"}
            )

        assert result is mock_404
        assert mock_get.call_count == 1

    @patch("src.cedar_mcp.external_api.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep: MagicMock):
        """Should use exponential backoff: delay * 2^attempt."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {}

        mock_200 = MagicMock()
        mock_200.status_code = 200

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            side_effect=[mock_429, mock_429, mock_200],
        ):
            result = _request_with_retry(
                "https://example.com",
                headers={"Authorization": "test"},
                initial_delay=1.0,
            )

        assert result is mock_200
        # First retry: 1.0 * 2^0 = 1.0, second: 1.0 * 2^1 = 2.0
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0

    @patch("src.cedar_mcp.external_api.time.sleep")
    def test_passes_params_and_timeout(self, mock_sleep: MagicMock):
        """Should pass params and timeout through to requests.get."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            return_value=mock_response,
        ) as mock_get:
            _request_with_retry(
                "https://example.com",
                headers={"Authorization": "test"},
                params={"q": "search"},
                timeout=30,
            )

        mock_get.assert_called_once_with(
            "https://example.com",
            headers={"Authorization": "test"},
            params={"q": "search"},
            timeout=30,
        )

    @patch("src.cedar_mcp.external_api.time.sleep")
    def test_delay_capped_at_max_delay(self, mock_sleep: MagicMock):
        """Should cap the delay at max_delay even if Retry-After is larger."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "3600"}

        mock_200 = MagicMock()
        mock_200.status_code = 200

        with patch(
            "src.cedar_mcp.external_api.requests.get",
            side_effect=[mock_429, mock_200],
        ):
            result = _request_with_retry(
                "https://example.com",
                headers={"Authorization": "test"},
                max_delay=10.0,
            )

        assert result is mock_200
        mock_sleep.assert_called_once_with(10.0)

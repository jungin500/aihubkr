#!/usr/bin/env python3
#
# AIHub Authentication Tests
# Unit tests for API key authentication with custom success/failure conditions
#
# - Tests API key validation with HTTP 502 responses
# - Validates success/failure based on response content
# - Tests credential management and storage
# - Mocks API responses for controlled testing
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

import os
from unittest.mock import Mock, patch

import pytest
import requests
import responses

from src.aihubkr.core.auth import AIHubAuth
from src.aihubkr.core.config import AIHubConfig


class TestAIHubAuth:
    """Test cases for AIHub authentication module."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        api_key = "test-api-key-12345"
        auth = AIHubAuth(api_key)
        assert auth.api_key == api_key
        assert auth.autosave_enabled is False

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        auth = AIHubAuth()
        assert auth.api_key is None
        assert auth.autosave_enabled is False

    def test_set_api_key(self):
        """Test setting API key."""
        auth = AIHubAuth()
        api_key = "new-api-key-67890"
        auth.set_api_key(api_key)
        assert auth.api_key == api_key

    def test_set_api_key_with_autosave(self):
        """Test setting API key with autosave enabled."""
        auth = AIHubAuth()
        auth.autosave_enabled = True

        with patch.object(auth, 'save_credential') as mock_save:
            api_key = "new-api-key-67890"
            auth.set_api_key(api_key)
            mock_save.assert_called_once()

    def test_get_auth_headers_with_api_key(self):
        """Test getting authentication headers with API key."""
        api_key = "test-api-key-12345"
        auth = AIHubAuth(api_key)
        headers = auth.get_auth_headers()
        assert headers == {"apikey": api_key}

    def test_get_auth_headers_without_api_key(self):
        """Test getting authentication headers without API key."""
        auth = AIHubAuth()
        headers = auth.get_auth_headers()
        assert headers is None

    @responses.activate
    def test_validate_api_key_always_fails_with_502(self):
        """Test API key validation always fails with HTTP 502 response (real API behavior)."""
        # Mock the API key validation endpoint with real failure message
        responses.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/-1.do",
            body="요청하신 데이터셋의 파일이 존재하지 않습니다. 파일의 존재여부 및 자세한 사항은 홈페이지(https://aihub.or.kr)에서 확인 바랍니다.",
            status=502,  # Always 502 and always indicates failure
            content_type="text/plain"
        )

        auth = AIHubAuth("valid-api-key")
        result = auth.validate_api_key()
        # The validation endpoint always returns failure, even with valid API keys
        assert result is False

    @responses.activate
    def test_validate_api_key_failure_with_502(self):
        """Test API key validation failure with HTTP 502 response."""
        # Mock the API key validation endpoint with real failure message
        responses.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/-1.do",
            body="요청하신 데이터셋의 파일이 존재하지 않습니다. 파일의 존재여부 및 자세한 사항은 홈페이지(https://aihub.or.kr)에서 확인 바랍니다.",
            status=502,  # Always 502 but content indicates failure
            content_type="text/plain"
        )

        auth = AIHubAuth("invalid-api-key")
        result = auth.validate_api_key()
        assert result is False

    @responses.activate
    def test_validate_api_key_unknown_response(self):
        """Test API key validation with unknown response content."""
        # Mock the API key validation endpoint
        responses.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/-1.do",
            body="알 수 없는 응답입니다.",
            status=502,
            content_type="text/plain"
        )

        auth = AIHubAuth("unknown-api-key")
        result = auth.validate_api_key()
        assert result is False

    @responses.activate
    def test_validate_api_key_timeout(self):
        """Test API key validation with timeout."""
        # Mock the API key validation endpoint to timeout
        responses.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/-1.do",
            body=requests.Timeout("Request timed out"),
            status=408
        )

        auth = AIHubAuth("timeout-api-key")
        result = auth.validate_api_key()
        assert result is False

    @responses.activate
    def test_validate_api_key_network_error(self):
        """Test API key validation with network error."""
        # Mock the API key validation endpoint to fail
        responses.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/-1.do",
            body=requests.ConnectionError("Connection failed"),
            status=500
        )

        auth = AIHubAuth("network-error-api-key")
        result = auth.validate_api_key()
        assert result is False

    def test_validate_api_key_without_key(self):
        """Test API key validation without API key."""
        auth = AIHubAuth()
        result = auth.validate_api_key()
        assert result is False

    @patch.object(AIHubConfig, 'get_instance')
    def test_save_credential(self, mock_config_instance):
        """Test saving API key credentials."""
        mock_config = Mock()
        mock_config.config_db = {}
        mock_config_instance.return_value = mock_config

        auth = AIHubAuth("test-api-key")
        auth.save_credential()

        assert mock_config.config_db["api_key"] == "test-api-key"
        assert mock_config.config_db["version"] == "2"
        mock_config.save_to_disk.assert_called_once()

    def test_save_credential_without_api_key(self):
        """Test saving credentials without API key."""
        auth = AIHubAuth()
        # Should not raise an exception
        auth.save_credential()

    @patch.object(AIHubConfig, 'get_instance')
    def test_load_credentials_success(self, mock_config_instance):
        """Test loading credentials successfully."""
        mock_config = Mock()
        mock_config.config_db = {
            "api_key": "saved-api-key",
            "version": "2"
        }
        mock_config_instance.return_value = mock_config

        auth = AIHubAuth()
        result = auth.load_credentials()

        assert result == "saved-api-key"
        assert auth.api_key == "saved-api-key"
        assert auth.autosave_enabled is True

    @patch.object(AIHubConfig, 'get_instance')
    def test_load_credentials_outdated_version(self, mock_config_instance):
        """Test loading credentials with outdated version."""
        mock_config = Mock()
        mock_config.config_db = {
            "api_key": "old-api-key",
            "version": "1"  # Outdated version
        }
        mock_config.save_to_disk = Mock()
        mock_config.load_from_disk = Mock()
        mock_config_instance.return_value = mock_config

        auth = AIHubAuth()
        result = auth.load_credentials()

        assert result is None
        assert auth.api_key is None
        assert auth.autosave_enabled is False
        # Should clear the outdated credentials by calling pop on config_db
        assert "api_key" not in mock_config.config_db
        assert "version" not in mock_config.config_db
        mock_config.save_to_disk.assert_called_once()

    @patch.object(AIHubConfig, 'get_instance')
    def test_load_credentials_no_saved_key(self, mock_config_instance):
        """Test loading credentials when no key is saved."""
        mock_config = Mock()
        mock_config.config_db = {}
        mock_config_instance.return_value = mock_config

        auth = AIHubAuth()
        result = auth.load_credentials()

        assert result is None
        assert auth.api_key is None
        assert auth.autosave_enabled is False

    @patch.object(AIHubConfig, 'get_instance')
    def test_clear_credential(self, mock_config_instance):
        """Test clearing stored credentials."""
        mock_config = Mock()
        mock_config.config_db = {
            "api_key": "test-api-key",
            "version": "2"
        }
        mock_config.save_to_disk = Mock()
        mock_config.load_from_disk = Mock()
        mock_config_instance.return_value = mock_config

        auth = AIHubAuth("test-api-key")
        auth.autosave_enabled = True
        auth.clear_credential()

        assert auth.api_key is None
        assert auth.autosave_enabled is False
        # Should clear the credentials by calling pop on config_db
        assert "api_key" not in mock_config.config_db
        assert "version" not in mock_config.config_db
        mock_config.save_to_disk.assert_called_once()


class TestAIHubAuthIntegration:
    """Integration tests for AIHub authentication."""

    @pytest.mark.integration
    @pytest.mark.auth
    def test_full_authentication_flow(self):
        """Test complete authentication flow."""
        auth = AIHubAuth()

        # Test setting API key
        api_key = "integration-test-key"
        auth.set_api_key(api_key)
        assert auth.api_key == api_key

        # Test getting auth headers
        headers = auth.get_auth_headers()
        assert headers == {"apikey": api_key}

        # Test clearing credentials
        auth.clear_credential()
        assert auth.api_key is None
        assert auth.autosave_enabled is False

    @pytest.mark.api
    @pytest.mark.slow
    def test_real_api_key_validation(self):
        """Test with real API key validation (marked as slow)."""
        # This test requires a real API key and internet connection
        # It's marked as slow and should be run separately
        api_key = os.getenv("AIHUB_TEST_API_KEY")
        if not api_key:
            pytest.skip("AIHUB_TEST_API_KEY environment variable not set")

        auth = AIHubAuth(api_key)
        result = auth.validate_api_key()

        # Should return a boolean (True for valid, False for invalid)
        assert isinstance(result, bool)

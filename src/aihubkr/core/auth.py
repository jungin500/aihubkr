#!/usr/bin/env python3
#
# AIHub Authentication Module
# Handles API key authentication for AIHub API
#
# - Replaces username/password authentication with API key authentication
# - Validates API key with AIHub server
# - Manages API key storage and retrieval
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

from typing import Dict, Optional

import requests
from .config import AIHubConfig


class AIHubAuth:
    """Handles API key authentication for AIHub API."""

    BASE_URL = "https://api.aihub.or.kr"
    KEY_VALIDATE_URL = f"{BASE_URL}/down/0.5/-1.do"
    CREDENTIAL_VERSION = "2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.autosave_enabled = False

    def clear_credential(self) -> None:
        """Clear stored API key credentials."""
        self.api_key = None
        self.autosave_enabled = False

        config_manager = AIHubConfig.get_instance()
        if "api_key" in config_manager.config_db:
            config_manager.config_db.pop("api_key")
        if "version" in config_manager.config_db:
            config_manager.config_db.pop("version")
        config_manager.save_to_disk()

    def save_credential(self) -> None:
        """Save API key and version to configuration."""
        if not self.api_key:
            return

        config_manager = AIHubConfig.get_instance()
        config_manager.config_db["api_key"] = self.api_key
        config_manager.config_db["version"] = self.CREDENTIAL_VERSION
        config_manager.save_to_disk()

    def load_credentials(self) -> Optional[str]:
        """Load API key from configuration, check version, and migrate if needed."""
        config_manager = AIHubConfig.get_instance()
        config_manager.load_from_disk()

        api_key = config_manager.config_db.get("api_key")
        version = config_manager.config_db.get("version")
        if api_key and version == self.CREDENTIAL_VERSION:
            self.api_key = api_key
            self.autosave_enabled = True
            return api_key
        elif api_key and version != self.CREDENTIAL_VERSION:
            # Outdated credential, clear and require re-entry
            self.clear_credential()
            return None
        return None

    def validate_api_key(self) -> bool:
        """Validate API key with AIHub server."""
        if not self.api_key:
            return False

        try:
            response = requests.get(
                self.KEY_VALIDATE_URL,
                headers={"apikey": self.api_key},
                timeout=30  # Add 30 second timeout
            )

            # We don't trust the KEY_VALIDATE_URL's response code.
            # It's always 502 Bad gateway!

            response_body = response.text.strip()
            success_candidates = ["요청하신", "파일"]
            failure_candidates = ["인증", "권한"]

            def check_success(body: str) -> bool:
                """Check if the response body contains a success message."""
                for candidate in success_candidates:
                    if candidate in body:
                        return True
                return False

            def check_failure(body: str) -> bool:
                """Check if the response body contains a failure message."""
                for candidate in failure_candidates:
                    if candidate in body:
                        return True
                return False

            if check_success(response_body):
                return True
            elif check_failure(response_body):
                return False
            else:
                # Invalid response - or API changed?
                return False

        except requests.Timeout:
            return False
        except requests.RequestException as e:
            return False

    def get_auth_headers(self) -> Optional[Dict[str, str]]:
        """Get authentication headers for API requests."""
        if not self.api_key:
            return None

        # Don't validate on every request to avoid blocking
        # The API key should be validated when the user clicks "Validate API Key"
        return {"apikey": self.api_key}

    def set_api_key(self, api_key: str) -> None:
        """Set API key and optionally save it."""
        self.api_key = api_key
        if self.autosave_enabled:
            self.save_credential()

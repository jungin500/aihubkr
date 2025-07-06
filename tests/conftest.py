#!/usr/bin/env python3
#
# AIHubKR Test Configuration
# Shared fixtures and test utilities for AIHub API testing
#
# - Common test fixtures for API mocking
# - Response simulation utilities
# - Test data and constants
# - Custom success/failure condition helpers
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

import os
import tempfile
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import Mock

import pytest
import responses


class AIHubTestResponses:
    """Test response data for AIHub API endpoints."""

    # API Key Validation Responses (always HTTP 502 but content determines success)
    VALID_API_KEY_RESPONSE = """UTF-8
output normally
modify the character information
요청하신 파일을 다운로드할 수 있습니다.
파일 다운로드를 시작합니다."""

    INVALID_API_KEY_RESPONSE = """UTF-8
output normally
modify the character information
인증에 실패했습니다.
권한이 없습니다."""

    UNKNOWN_API_KEY_RESPONSE = """UTF-8
output normally
modify the character information
알 수 없는 오류가 발생했습니다."""

    # Dataset List Response
    DATASET_LIST_RESPONSE = """UTF-8
output normally
modify the character information
================================================================================
공지사항
================================================================================

================================================================================
데이터셋 목록
================================================================================
001,한국어 대화 데이터셋
002,이미지 분류 데이터셋
003,텍스트 분석 데이터셋
================================================================================
"""

    # File Tree Response
    FILE_TREE_RESPONSE = """UTF-8
output normally
modify the character information
dataset_001
├── README.txt | 1.5KB | 1
├── data/
│   ├── train/
│   │   ├── file1.txt | 2.3MB | 2
│   │   └── file2.txt | 1.8MB | 3
│   └── test/
│       └── test.txt | 500KB | 4
└── metadata.json | 15KB | 5"""

    # Download Response (successful)
    DOWNLOAD_SUCCESS_RESPONSE = """UTF-8
output normally
modify the character information
다운로드가 시작됩니다.
파일 크기: 1.5GB
예상 시간: 5분"""

    # Download Response (failure)
    DOWNLOAD_FAILURE_RESPONSE = """UTF-8
output normally
modify the character information
다운로드에 실패했습니다.
권한이 없거나 파일이 존재하지 않습니다."""


class AIHubTestUtils:
    """Utility functions for AIHub API testing."""

    @staticmethod
    def create_mock_response(
        status_code: int,
        content: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Mock:
        """Create a mock response object for testing."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = content
        mock_response.headers = headers or {}
        return mock_response

    @staticmethod
    def validate_success_conditions(response_text: str) -> bool:
        """Validate if response indicates success based on AIHub API patterns."""
        success_indicators = [
            "요청하신",
            "파일",
            "다운로드",
            "시작",
            "완료"
        ]

        failure_indicators = [
            "인증",
            "권한",
            "실패",
            "오류",
            "없습니다"
        ]

        # Check for success indicators
        for indicator in success_indicators:
            if indicator in response_text:
                return True

        # Check for failure indicators
        for indicator in failure_indicators:
            if indicator in response_text:
                return False

        # Default to failure if no clear indicators
        return False

    @staticmethod
    def get_test_api_key() -> str:
        """Get a test API key for testing purposes."""
        return "test-api-key-12345"

    @staticmethod
    def get_test_dataset_key() -> str:
        """Get a test dataset key for testing purposes."""
        return "001"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_api_responses():
    """Mock AIHub API responses for testing."""
    with responses.RequestsMock() as rsps:
        # Mock API key validation endpoint
        rsps.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/-1.do",
            body=AIHubTestResponses.VALID_API_KEY_RESPONSE,
            status=502,  # Always 502 but content determines success
            content_type="text/plain"
        )

        # Mock dataset list endpoint
        rsps.add(
            responses.GET,
            "https://api.aihub.or.kr/info/dataset.do",
            body=AIHubTestResponses.DATASET_LIST_RESPONSE,
            status=200,
            content_type="text/plain"
        )

        # Mock file tree endpoint
        rsps.add(
            responses.GET,
            "https://api.aihub.or.kr/info/001.do",
            body=AIHubTestResponses.FILE_TREE_RESPONSE,
            status=200,
            content_type="text/plain"
        )

        # Mock download endpoint
        rsps.add(
            responses.GET,
            "https://api.aihub.or.kr/down/0.5/001/all",
            body=AIHubTestResponses.DOWNLOAD_SUCCESS_RESPONSE,
            status=200,
            content_type="text/plain"
        )

        yield rsps


@pytest.fixture
def test_api_key():
    """Provide a test API key."""
    return AIHubTestUtils.get_test_api_key()


@pytest.fixture
def test_dataset_key():
    """Provide a test dataset key."""
    return AIHubTestUtils.get_test_dataset_key()


@pytest.fixture
def auth_headers(test_api_key):
    """Provide authentication headers for testing."""
    return {"apikey": test_api_key}


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config_data = {
        "api_key": "test-api-key-12345",
        "version": "2"
    }
    return config_data


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set test environment variables
    os.environ["AIHUB_APIKEY"] = "test-api-key-12345"

    yield

    # Cleanup
    if "AIHUB_APIKEY" in os.environ:
        del os.environ["AIHUB_APIKEY"]

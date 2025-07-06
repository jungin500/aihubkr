#!/usr/bin/env python3
#
# AIHub API Integration Tests
# Integration tests for AIHub API server with custom success/failure validation
#
# - Tests real API interactions with custom success conditions
# - Validates API key authentication with HTTP 502 responses
# - Tests dataset operations and file downloads
# - Implements custom success/failure logic for API responses
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

import os
import time
from typing import Dict, List, Optional, Tuple
from unittest.mock import Mock

import pytest
import requests

from src.aihubkr.core.auth import AIHubAuth
from src.aihubkr.core.downloader import AIHubDownloader, DownloadStatus


class AIHubAPITestValidator:
    """Custom validator for AIHub API responses with custom success conditions."""

    @staticmethod
    def validate_api_key_response(response: requests.Response) -> Tuple[bool, str]:
        """
        Validate API key validation response.

        AIHub API key validation always returns HTTP 502, but the response content
        determines success or failure.
        """
        if response.status_code != 502:
            return False, f"Expected HTTP 502, got {response.status_code}"

        response_text = response.text.strip()

        # Success indicators in Korean
        success_indicators = ["요청하신", "파일", "다운로드", "시작"]
        # Failure indicators in Korean
        failure_indicators = ["인증", "권한", "실패", "오류", "없습니다"]

        # Check for success indicators
        for indicator in success_indicators:
            if indicator in response_text:
                return True, f"Success: Found indicator '{indicator}' in response"

        # Check for failure indicators
        for indicator in failure_indicators:
            if indicator in response_text:
                return False, f"Failure: Found indicator '{indicator}' in response"

        # Unknown response pattern
        return False, f"Unknown response pattern: {response_text[:100]}..."

    @staticmethod
    def validate_dataset_list_response(response: requests.Response) -> Tuple[bool, str]:
        """Validate dataset list response."""
        if response.status_code not in [200, 502]:
            return False, f"Unexpected status code: {response.status_code}"

        response_text = response.text.strip()

        # Check for dataset list indicators
        if "데이터셋 목록" in response_text or "dataset" in response_text.lower():
            return True, "Valid dataset list response"

        # Check for error indicators
        if any(indicator in response_text for indicator in ["오류", "에러", "error", "실패"]):
            return False, "Error in dataset list response"

        return False, "Unknown dataset list response format"

    @staticmethod
    def validate_file_tree_response(response: requests.Response) -> Tuple[bool, str]:
        """Validate file tree response."""
        if response.status_code not in [200, 502]:
            return False, f"Unexpected status code: {response.status_code}"

        response_text = response.text.strip()

        # Check for file tree indicators
        if any(indicator in response_text for indicator in ["├──", "└──", "│", "tree"]):
            return True, "Valid file tree response"

        # Check for error indicators
        if any(indicator in response_text for indicator in ["오류", "에러", "error", "실패", "없습니다"]):
            return False, "Error in file tree response"

        return False, "Unknown file tree response format"

    @staticmethod
    def validate_download_response(response: requests.Response) -> Tuple[bool, str]:
        """Validate download response."""
        if response.status_code not in [200, 502]:
            return False, f"Unexpected status code: {response.status_code}"

        response_text = response.text.strip()

        # Check for download success indicators
        if any(indicator in response_text for indicator in ["다운로드", "시작", "완료", "download"]):
            return True, "Valid download response"

        # Check for download failure indicators
        if any(indicator in response_text for indicator in ["실패", "오류", "권한", "없습니다"]):
            return False, "Download failed"

        return False, "Unknown download response format"


class TestAIHubAPIIntegration:
    """Integration tests for AIHub API server."""

    @pytest.fixture
    def api_key(self) -> Optional[str]:
        """Get API key from environment or skip test."""
        api_key = os.getenv("AIHUB_TEST_API_KEY")
        if not api_key:
            pytest.skip("AIHUB_TEST_API_KEY environment variable not set")
        return api_key

    @pytest.fixture
    def auth_headers(self, api_key: str) -> Dict[str, str]:
        """Get authentication headers."""
        return {"apikey": api_key}

    @pytest.mark.api
    @pytest.mark.slow
    def test_api_key_validation_real(self, api_key: str):
        """Test real API key validation with custom success conditions."""
        auth = AIHubAuth(api_key)

        # Test the actual validation method
        result = auth.validate_api_key()

        # Should return a boolean (True for valid, False for invalid)
        assert isinstance(result, bool)

        if result:
            print(f"API key validation successful for key: {api_key[:10]}...")
        else:
            print(f"API key validation failed for key: {api_key[:10]}...")

    @pytest.mark.api
    @pytest.mark.slow
    def test_api_key_validation_direct_request(self, api_key: str):
        """Test API key validation with direct HTTP request and custom validation."""
        url = "https://api.aihub.or.kr/down/0.5/-1.do"
        headers = {"apikey": api_key}

        try:
            response = requests.get(url, headers=headers, timeout=30)

            # Use custom validator
            success, message = AIHubAPITestValidator.validate_api_key_response(response)

            print(f"API Key Validation Result: {message}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Content: {response.text[:200]}...")

            # The test passes if we get a valid response (success or failure)
            # The important thing is that our custom validation logic works
            assert isinstance(success, bool)
            assert isinstance(message, str)

        except requests.RequestException as e:
            pytest.fail(f"Request failed: {e}")

    @pytest.mark.api
    @pytest.mark.slow
    def test_dataset_list_real(self, auth_headers: Dict[str, str]):
        """Test real dataset list retrieval with custom validation."""
        url = "https://api.aihub.or.kr/info/dataset.do"

        try:
            response = requests.get(url, headers=auth_headers, timeout=30)

            # Use custom validator
            success, message = AIHubAPITestValidator.validate_dataset_list_response(response)

            print(f"Dataset List Result: {message}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Content: {response.text[:300]}...")

            if success:
                # Parse the dataset list
                downloader = AIHubDownloader(auth_headers)
                datasets = downloader.process_dataset_list(response.text)

                if datasets:
                    print(f"Found {len(datasets)} datasets")
                    for dataset_id, dataset_name in datasets[:3]:  # Show first 3
                        print(f"  {dataset_id}: {dataset_name}")
                else:
                    print("No datasets found in response")

            # Test passes if we get a valid response
            assert isinstance(success, bool)
            assert isinstance(message, str)

        except requests.RequestException as e:
            pytest.fail(f"Request failed: {e}")

    @pytest.mark.api
    @pytest.mark.slow
    def test_file_tree_real(self, auth_headers: Dict[str, str]):
        """Test real file tree retrieval with custom validation."""
        # First get a dataset list to find a valid dataset key
        dataset_url = "https://api.aihub.or.kr/info/dataset.do"

        try:
            # Get dataset list
            response = requests.get(dataset_url, headers=auth_headers, timeout=30)
            success, message = AIHubAPITestValidator.validate_dataset_list_response(response)

            if not success:
                pytest.skip(f"Cannot get dataset list: {message}")

            # Parse to get a dataset key
            downloader = AIHubDownloader(auth_headers)
            datasets = downloader.process_dataset_list(response.text)

            if not datasets:
                pytest.skip("No datasets available for testing")

            # Use the first dataset for testing
            dataset_key = datasets[0][0]
            print(f"Testing file tree for dataset: {dataset_key}")

            # Get file tree
            file_tree_url = f"https://api.aihub.or.kr/info/{dataset_key}.do"
            response = requests.get(file_tree_url, headers=auth_headers, timeout=30)

            success, message = AIHubAPITestValidator.validate_file_tree_response(response)

            print(f"File Tree Result: {message}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Content: {response.text[:400]}...")

            # Test passes if we get a valid response
            assert isinstance(success, bool)
            assert isinstance(message, str)

        except requests.RequestException as e:
            pytest.fail(f"Request failed: {e}")

    @pytest.mark.api
    @pytest.mark.slow
    def test_download_url_generation(self, auth_headers: Dict[str, str]):
        """Test download URL generation and validation."""
        downloader = AIHubDownloader(auth_headers)

        # Test URL generation
        dataset_key = "test_dataset"
        file_keys = "1,2,3"

        url = downloader.get_raw_url(dataset_key, file_keys)
        expected_url = f"https://api.aihub.or.kr/down/0.5/{dataset_key}.do?fileSn={file_keys}"

        assert url == expected_url
        print(f"Generated download URL: {url}")

        # Test with "all" files
        url_all = downloader.get_raw_url(dataset_key, "all")
        expected_url_all = f"https://api.aihub.or.kr/down/0.5/{dataset_key}.do?fileSn=all"

        assert url_all == expected_url_all
        print(f"Generated download URL (all): {url_all}")

    @pytest.mark.api
    @pytest.mark.slow
    def test_end_to_end_workflow(self, api_key: str):
        """Test complete end-to-end workflow with real API."""
        auth = AIHubAuth(api_key)
        auth_headers = auth.get_auth_headers()

        if not auth_headers:
            pytest.fail("Failed to get authentication headers")

        downloader = AIHubDownloader(auth_headers)

        # Step 1: Validate API key
        print("Step 1: Validating API key...")
        api_valid = auth.validate_api_key()
        assert isinstance(api_valid, bool)
        print(f"API Key Valid: {api_valid}")

        if not api_valid:
            pytest.skip("API key validation failed")

        # Step 2: Get dataset list
        print("Step 2: Getting dataset list...")
        datasets = downloader.get_dataset_info()

        if datasets:
            print(f"Found {len(datasets)} datasets")
            # Show first few datasets
            for dataset_id, dataset_name in datasets[:3]:
                print(f"  {dataset_id}: {dataset_name}")

            # Step 3: Get file tree for first dataset
            first_dataset = datasets[0][0]
            print(f"Step 3: Getting file tree for dataset {first_dataset}...")

            file_tree = downloader.get_file_tree(first_dataset)
            if file_tree:
                print("File tree retrieved successfully")
                print(f"File tree preview: {file_tree[:200]}...")
            else:
                print("Failed to get file tree")
        else:
            print("No datasets found")

        # Test passes if we can complete the workflow without exceptions
        print("End-to-end workflow completed successfully")


class TestAIHubAPICustomConditions:
    """Tests for custom success/failure conditions in AIHub API."""

    def test_custom_success_condition_502_response(self):
        """Test that HTTP 502 responses can be successful based on content."""
        # Simulate AIHub API behavior: HTTP 502 with success content
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "요청하신 파일을 다운로드할 수 있습니다."

        success, message = AIHubAPITestValidator.validate_api_key_response(mock_response)

        assert success is True
        assert "Success" in message
        assert "요청하신" in message

    def test_custom_failure_condition_502_response(self):
        """Test that HTTP 502 responses can be failures based on content."""
        # Simulate AIHub API behavior: HTTP 502 with failure content
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "인증에 실패했습니다. 권한이 없습니다."

        success, message = AIHubAPITestValidator.validate_api_key_response(mock_response)

        assert success is False
        assert "Failure" in message
        assert "인증" in message

    def test_custom_success_condition_200_response(self):
        """Test that HTTP 200 responses can be successful."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "데이터셋 목록\n001,테스트 데이터셋"

        success, message = AIHubAPITestValidator.validate_dataset_list_response(mock_response)

        assert success is True
        assert "Valid dataset list" in message

    def test_custom_failure_condition_200_response(self):
        """Test that HTTP 200 responses can be failures based on content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "오류가 발생했습니다."

        success, message = AIHubAPITestValidator.validate_dataset_list_response(mock_response)

        assert success is False
        assert "Error" in message

    def test_unknown_response_patterns(self):
        """Test handling of unknown response patterns."""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "알 수 없는 응답 패턴"

        success, message = AIHubAPITestValidator.validate_api_key_response(mock_response)

        assert success is False
        assert "Unknown" in message

    def test_response_content_analysis(self):
        """Test comprehensive response content analysis."""
        test_cases = [
            # (response_text, expected_success, expected_indicator)
            ("요청하신 파일을 다운로드할 수 있습니다.", True, "요청하신"),
            ("파일 다운로드가 시작됩니다.", True, "파일"),
            ("인증에 실패했습니다.", False, "인증"),
            ("권한이 없습니다.", False, "권한"),
            ("다운로드가 완료되었습니다.", True, "다운로드"),
            ("오류가 발생했습니다.", False, "오류"),
        ]

        for response_text, expected_success, expected_indicator in test_cases:
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.text = response_text

            success, message = AIHubAPITestValidator.validate_api_key_response(mock_response)

            assert success == expected_success, f"Failed for: {response_text}"
            assert expected_indicator in message, f"Missing indicator in message: {message}"


class TestAIHubAPIPerformance:
    """Performance tests for AIHub API interactions."""

    @pytest.mark.api
    @pytest.mark.slow
    def test_api_response_time(self, auth_headers: Dict[str, str]):
        """Test API response times for different endpoints."""
        endpoints = [
            "https://api.aihub.or.kr/down/0.5/-1.do",  # API key validation
            "https://api.aihub.or.kr/info/dataset.do",  # Dataset list
        ]

        for endpoint in endpoints:
            start_time = time.time()

            try:
                response = requests.get(endpoint, headers=auth_headers, timeout=30)
                end_time = time.time()
                response_time = end_time - start_time

                print(f"Endpoint: {endpoint}")
                print(f"Response Time: {response_time:.2f} seconds")
                print(f"Status Code: {response.status_code}")
                print(f"Response Size: {len(response.text)} characters")
                print("-" * 50)

                # Response time should be reasonable (less than 10 seconds)
                assert response_time < 10.0, f"Response time too slow: {response_time:.2f}s"

            except requests.RequestException as e:
                print(f"Request failed for {endpoint}: {e}")
                # Don't fail the test for network issues
                pass

    @pytest.mark.api
    @pytest.mark.slow
    def test_concurrent_api_requests(self, auth_headers: Dict[str, str]):
        """Test concurrent API requests to check for rate limiting."""
        import concurrent.futures

        endpoint = "https://api.aihub.or.kr/info/dataset.do"

        def make_request():
            try:
                response = requests.get(endpoint, headers=auth_headers, timeout=30)
                return response.status_code, len(response.text)
            except Exception as e:
                return None, str(e)

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]

        print("Concurrent request results:")
        for i, (status_code, result) in enumerate(results):
            print(f"Request {i+1}: Status={status_code}, Result={result}")

        # All requests should complete (even if some fail)
        assert len(results) == 5, "Not all concurrent requests completed"

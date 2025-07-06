#!/usr/bin/env python3
#
# AIHubKR Test Suite
# Comprehensive test suite for AIHub API server interactions
#
# - Unit tests for core modules
# - Integration tests for API interactions
# - Mock-based tests for API response validation
# - Custom success/failure condition testing
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

"""
AIHubKR Test Suite

This test suite validates the AIHub API server interactions with custom success/failure
conditions that account for the API's unique behavior patterns.

Key Testing Principles:
1. API responses with HTTP 502 (Bad Gateway) can still be "successful" based on content
2. Success/failure is determined by response text analysis, not HTTP status codes
3. Authentication validation uses specific response patterns
4. File downloads and dataset operations have different validation criteria

Test Categories:
- Unit Tests: Individual module functionality
- Integration Tests: End-to-end API interactions
- Mock Tests: Controlled API response simulation
- API Tests: Real API server validation (marked as slow)
"""

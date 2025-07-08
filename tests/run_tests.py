#!/usr/bin/env python3
#
# AIHub Test Runner
# Test runner script for AIHub API testing framework
#
# - Demonstrates how to run different test categories
# - Shows custom success/failure condition testing
# - Provides examples of API server validation
# - Explains the testing framework architecture
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

"""
AIHub API Testing Framework

This script demonstrates how to run the comprehensive test suite for the AIHub API server
with custom success/failure conditions that account for the API's unique behavior patterns.

Key Features:
1. Custom Success/Failure Conditions: Tests validate responses based on content, not HTTP status codes
2. API Key Validation: Tests the unique HTTP 502 response pattern for API key validation
3. Mock and Real API Testing: Both controlled mock tests and real API integration tests
4. Performance Testing: Response time and concurrent request validation
5. Comprehensive Coverage: Unit, integration, and end-to-end testing

Test Categories:
- Unit Tests: Individual module functionality (fast)
- Integration Tests: End-to-end workflows with mocks (medium)
- API Tests: Real API server interactions (slow, requires API key)
- Performance Tests: Response time and concurrency (slow)

Usage Examples:
    python tests/run_tests.py --unit                    # Run unit tests only
    python tests/run_tests.py --integration             # Run integration tests
    python tests/run_tests.py --api                     # Run real API tests (requires API key)
    python tests/run_tests.py --all                     # Run all tests
    python tests/run_tests.py --custom-conditions       # Test custom success/failure logic
    python tests/run_tests.py --performance             # Run performance tests
"""

import argparse
import os
import subprocess
import sys
import json
import time
from pathlib import Path


def create_test_directories():
    """Create directories for test results."""
    directories = ["test-results", "performance-logs", "custom-condition-logs"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")


def run_pytest_command(args, markers=None, verbose=False, log_file=None):
    """Run pytest with specified arguments and markers."""
    cmd = [sys.executable, "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if markers:
        cmd.extend(["-m", markers])

    cmd.extend(args)

    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)

    # Capture output if log_file is specified
    if log_file:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent,
                                capture_output=True, text=True)

        # Write to log file
        with open(log_file, "w") as f:
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 80 + "\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\nSTDERR:\n")
                f.write(result.stderr)

        # Also print to console
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return result.returncode
    else:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode


def check_api_key():
    """Check if API key is available for real API tests."""
    api_key = os.getenv("AIHUB_TEST_API_KEY")
    if not api_key:
        print("Warning: AIHUB_TEST_API_KEY environment variable not set.")
        print("Real API tests will be skipped.")
        print("Set the environment variable to run real API tests:")
        print("  export AIHUB_TEST_API_KEY='your-api-key-here'")
        return False
    return True


def run_unit_tests(verbose=False):
    """Run unit tests."""
    print("Running Unit Tests")
    print("=" * 50)
    print("Testing individual module functionality...")

    return run_pytest_command(
        ["tests/"],
        verbose=verbose,
        log_file="test-results/unit-tests.log"
    )


def run_integration_tests(verbose=False):
    """Run integration tests."""
    print("Running Integration Tests")
    print("=" * 50)
    print("Testing end-to-end workflows with mocked API responses...")

    return run_pytest_command(
        ["tests/"],
        markers="integration",
        verbose=verbose,
        log_file="test-results/integration-tests.log"
    )


def run_api_tests(verbose=False):
    """Run real API tests."""
    print("Running Real API Tests")
    print("=" * 50)

    if not check_api_key():
        print("Skipping real API tests due to missing API key.")
        return 0

    print("Testing real AIHub API server interactions...")
    print("Note: These tests require internet connection and valid API key.")

    # Create test directories
    create_test_directories()

    return run_pytest_command(
        ["tests/"],
        markers="api",
        verbose=verbose,
        log_file="test-results/api-tests.log"
    )


def run_custom_conditions_tests(verbose=False):
    """Run tests for custom success/failure conditions."""
    print("Running Custom Success/Failure Condition Tests")
    print("=" * 50)
    print("Testing custom validation logic for AIHub API responses...")

    # Create test directories
    create_test_directories()

    return run_pytest_command(
        ["tests/test_api_integration.py::TestAIHubAPICustomConditions"],
        verbose=verbose,
        log_file="custom-condition-logs/custom-conditions.log"
    )


def run_performance_tests(verbose=False):
    """Run performance tests."""
    print("Running Performance Tests")
    print("=" * 50)
    print("Testing API response times and concurrent requests...")

    if not check_api_key():
        print("Skipping performance tests due to missing API key.")
        return 0

    # Create test directories
    create_test_directories()

    return run_pytest_command(
        ["tests/test_api_integration.py::TestAIHubAPIPerformance"],
        verbose=verbose,
        log_file="performance-logs/performance-tests.log"
    )


def run_auth_tests(verbose=False):
    """Run authentication tests."""
    print("Running Authentication Tests")
    print("=" * 50)
    print("Testing API key validation and authentication flows...")

    return run_pytest_command(
        ["tests/test_auth.py"],
        verbose=verbose,
        log_file="test-results/auth-tests.log"
    )


def run_downloader_tests(verbose=False):
    """Run downloader tests."""
    print("Running Downloader Tests")
    print("=" * 50)
    print("Testing dataset download and file processing...")

    return run_pytest_command(
        ["tests/test_downloader.py"],
        verbose=verbose,
        log_file="test-results/downloader-tests.log"
    )


def run_parser_tests(verbose=False):
    """Run file list parser tests."""
    print("Running File List Parser Tests")
    print("=" * 50)
    print("Testing tree structure parsing and file information extraction...")

    return run_pytest_command(
        ["tests/test_filelist_parser.py"],
        verbose=verbose,
        log_file="test-results/parser-tests.log"
    )


def run_cli_tests(verbose=False):
    """Run CLI tests."""
    print("Running CLI Tests")
    print("=" * 50)
    print("Testing command-line interface functionality...")

    return run_pytest_command(
        ["tests/test_cli.py"],
        verbose=verbose,
        log_file="test-results/cli-tests.log"
    )


def run_coverage_tests(verbose=False):
    """Run tests with coverage reporting."""
    print("Running Tests with Coverage")
    print("=" * 50)
    print("Testing with code coverage analysis...")

    return run_pytest_command(
        ["tests/", "--cov=src/aihubkr", "--cov-report=term-missing", "--cov-report=html"],
        verbose=verbose,
        log_file="test-results/coverage-tests.log"
    )


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="AIHub API Testing Framework Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Run real API tests (requires API key)"
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run authentication tests"
    )
    parser.add_argument(
        "--downloader",
        action="store_true",
        help="Run downloader tests"
    )
    parser.add_argument(
        "--parser",
        action="store_true",
        help="Run file list parser tests"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run CLI tests"
    )
    parser.add_argument(
        "--custom-conditions",
        action="store_true",
        help="Run custom success/failure condition tests"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # If no specific test type is selected, show help
    if not any([
        args.unit, args.integration, args.api, args.auth, args.downloader,
        args.parser, args.cli, args.custom_conditions, args.performance,
        args.coverage, args.all
    ]):
        parser.print_help()
        return 1

    print("AIHub API Testing Framework")
    print("=" * 80)
    print("Testing AIHub API server with custom success/failure conditions")
    print("=" * 80)
    print()

    exit_codes = []

    try:
        if args.all:
            # Run all test categories
            test_functions = [
                run_unit_tests,
                run_integration_tests,
                run_auth_tests,
                run_downloader_tests,
                run_parser_tests,
                run_cli_tests,
                run_custom_conditions_tests,
                run_api_tests,
                run_performance_tests,
            ]

            for test_func in test_functions:
                exit_code = test_func(args.verbose)
                exit_codes.append(exit_code)
                print()
        else:
            # Run specific test categories
            if args.unit:
                exit_codes.append(run_unit_tests(args.verbose))

            if args.integration:
                exit_codes.append(run_integration_tests(args.verbose))

            if args.api:
                exit_codes.append(run_api_tests(args.verbose))

            if args.auth:
                exit_codes.append(run_auth_tests(args.verbose))

            if args.downloader:
                exit_codes.append(run_downloader_tests(args.verbose))

            if args.parser:
                exit_codes.append(run_parser_tests(args.verbose))

            if args.cli:
                exit_codes.append(run_cli_tests(args.verbose))

            if args.custom_conditions:
                exit_codes.append(run_custom_conditions_tests(args.verbose))

            if args.performance:
                exit_codes.append(run_performance_tests(args.verbose))

            if args.coverage:
                exit_codes.append(run_coverage_tests(args.verbose))

        print("=" * 80)
        print("Test Summary")
        print("=" * 80)

        if exit_codes:
            failed_tests = sum(1 for code in exit_codes if code != 0)
            total_tests = len(exit_codes)

            if failed_tests == 0:
                print(f"✅ All {total_tests} test categories passed!")
                return 0
            else:
                print(f"❌ {failed_tests}/{total_tests} test categories failed.")
                return 1
        else:
            print("No tests were run.")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError during test execution: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

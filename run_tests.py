#!/usr/bin/env python3
"""
Test runner script for CEDAR MCP integration tests.

This script provides convenient ways to run different categories of tests
and ensures proper environment setup.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def check_environment():
    """Check if the test environment is properly set up."""
    env_file = Path(".env.test")
    if not env_file.exists():
        print("❌ Error: .env.test file not found!")
        print("Please create .env.test with your API keys:")
        print("CEDAR_API_KEY=your-cedar-key")
        print("BIOPORTAL_API_KEY=your-bioportal-key")
        return False

    # Check if API keys are present
    from dotenv import load_dotenv

    load_dotenv(".env.test")

    cedar_key = os.getenv("CEDAR_API_KEY")
    bioportal_key = os.getenv("BIOPORTAL_API_KEY")

    if not cedar_key:
        print("❌ Error: CEDAR_API_KEY not found in .env.test")
        return False

    if not bioportal_key:
        print("❌ Error: BIOPORTAL_API_KEY not found in .env.test")
        return False

    print("✅ Environment check passed")
    return True


def run_pytest(args):
    """Run pytest with the given arguments."""
    cmd = ["python", "-m", "pytest"] + args
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="Run CEDAR MCP integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --unit            # Run only unit tests
  python run_tests.py --fast            # Run tests excluding slow ones
  python run_tests.py --coverage        # Run with coverage report
  python run_tests.py --external-api    # Run only external API tests
  python run_tests.py --processing      # Run only processing tests
  python run_tests.py --server          # Run only server tests
        """,
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests (requires API keys)",
    )
    parser.add_argument(
        "--unit", action="store_true", help="Run only unit tests (no API dependencies)"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Run tests excluding slow ones"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument(
        "--external-api", action="store_true", help="Run only external API tests"
    )
    parser.add_argument(
        "--processing", action="store_true", help="Run only processing tests"
    )
    parser.add_argument("--server", action="store_true", help="Run only server tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-warnings", action="store_true", help="Disable warnings")
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debugging mode (disable output capture)",
    )

    args = parser.parse_args()

    # Check environment if running integration tests
    if args.integration or not (args.unit or args.fast):
        if not check_environment():
            sys.exit(1)

    # Build pytest arguments
    pytest_args = []

    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")

    # Add warnings control
    if args.no_warnings:
        pytest_args.append("--disable-warnings")

    # Add debug mode (disable output capture)
    if args.debug:
        pytest_args.extend(["-s", "--tb=short"])

    # Add coverage
    if args.coverage:
        pytest_args.extend(
            ["--cov=src/cedar_mcp", "--cov-report=html", "--cov-report=term-missing"]
        )

    # Add test selection
    if args.integration:
        pytest_args.extend(["-m", "integration"])
    elif args.unit:
        pytest_args.extend(["-m", "unit"])
    elif args.fast:
        pytest_args.extend(["-m", "not slow"])

    # Add specific test files
    if args.external_api:
        pytest_args.append("test/test_external_api.py")
    elif args.processing:
        pytest_args.append("test/test_processing.py")
    elif args.server:
        pytest_args.append("test/test_server.py")
    else:
        pytest_args.append("test/")

    # Run the tests
    result = run_pytest(pytest_args)

    if result.returncode == 0:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code: {result.returncode}")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

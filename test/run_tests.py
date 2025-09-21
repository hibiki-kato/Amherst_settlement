#!/usr/bin/env python3
"""
Test runner script for the Amherst settlement optimization system.
Provides convenient commands for running different test suites.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print(f"{'=' * 60}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    original_dir = Path.cwd()

    try:
        # Change to script directory
        import os

        os.chdir(script_dir)

        # Add `src` directory to Python path
        src_dir = script_dir.parent / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        success = True

        if test_type in ["all", "basic"]:
            success &= run_command(
                "uv run pytest test_main.py -v", "Running all tests with verbose output"
            )

        if test_type in ["all", "coverage"]:
            success &= run_command(
                "uv run pytest test_main.py --cov=main --cov-report=term-missing",
                "Running tests with coverage report",
            )

        if test_type == "fast":
            success &= run_command(
                "uv run pytest test_main.py -x", "Running tests (fail fast)"
            )

        if test_type == "stage1":
            success &= run_command(
                "uv run pytest test_main.py::TestStage1MinAmount -v",
                "Testing Stage 1 optimization only",
            )

        if test_type == "stage2":
            success &= run_command(
                "uv run pytest test_main.py::TestStage2MinEdges -v",
                "Testing Stage 2 optimization only",
            )

        if test_type == "integration":
            success &= run_command(
                "uv run pytest test_main.py::TestIntegrationScenarios -v",
                "Testing integration scenarios only",
            )

        if test_type == "zelle_venmo_pairs":
            success &= run_command(
                "uv run pytest test_main.py::TestZelleVenmoPairs -v",
                "Testing Zelle and Venmo pairs",
            )

        if test_type == "help":
            print("""
🧪 Amherst Settlement Test Runner

Usage: python run_tests.py [TEST_TYPE]

Available test types:
  all         - Run all tests with coverage (default)
  basic       - Run all tests without coverage  
  coverage    - Run tests with detailed coverage report
  fast        - Run tests with fail-fast mode
  stage1      - Test only Stage 1 optimization
  stage2      - Test only Stage 2 optimization  
  integration - Test only integration scenarios
  help        - Show this help message

Examples:
  python run_tests.py
  python run_tests.py coverage
  python run_tests.py stage1
            """)
            return True

        if test_type not in [
            "all",
            "basic",
            "coverage",
            "fast",
            "stage1",
            "stage2",
            "integration",
            "help",
        ]:
            print(f"❌ Unknown test type: {test_type}")
            print("Run 'python run_tests.py help' for available options")
            return False

        # Final summary
        print(f"\n{'=' * 60}")
        if success:
            print("✅ All tests completed successfully!")
        else:
            print("❌ Some tests failed!")
        print(f"{'=' * 60}\n")

        return success

    finally:
        # Restore original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

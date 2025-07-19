#!/usr/bin/env python
"""
Test runner script for the Cox Tree Service Estimating Application.
"""
import sys
import subprocess
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run the test suite with coverage reporting."""
    print("Running Cox Tree Service Test Suite")
    print("=" * 50)
    
    # Set test environment variable
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=src",  # Coverage for src directory
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html",  # Generate HTML coverage report
        "--cov-fail-under=80",  # Fail if coverage < 80%
        "tests/"
    ]
    
    # Add specific test file if provided
    if len(sys.argv) > 1:
        cmd.append(sys.argv[1])
    
    # Run the tests
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
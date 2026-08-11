"""
Test Runner for Intelligence Graph

This script runs all tests for the intelligence graph, including:
1. Unit tests for individual nodes
2. Integration tests for the complete graph
3. Report quality tests
"""

import pytest
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """Run all tests for the intelligence graph."""
    print("🚀 Starting Intelligence Graph Test Suite")
    print("=" * 50)
    
    # Configure pytest to run async tests
    args = [
        "-v",  # Verbose output
        "-x",  # Exit on first failure
        "--tb=short",  # Short tracebacks
        "tests/"  # Test directory
    ]
    
    # Run tests
    exit_code = pytest.main(args)
    
    print("=" * 50)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Some tests failed. Exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    # Run the tests
    exit_code = run_tests()
    sys.exit(exit_code)
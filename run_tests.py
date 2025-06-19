#!/usr/bin/env python3
"""
Test runner for Broken Link Checker
Provides convenient commands to run different types of tests
"""

import sys
import subprocess
import argparse
import os


def run_command(cmd, description=""):
    """Run a command and return the result"""
    if description:
        print(f"\n🔍 {description}")
        print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def install_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    return run_command("pip install -r test_requirements.txt")


def run_unit_tests():
    """Run unit tests only"""
    cmd = "pytest test_broken_link_checker.py::TestBrokenLinkChecker -v"
    return run_command(cmd, "Running unit tests")


def run_integration_tests():
    """Run integration tests only"""
    cmd = "pytest test_broken_link_checker.py::TestBrokenLinkCheckerIntegration -v"
    return run_command(cmd, "Running integration tests")


def run_edge_case_tests():
    """Run edge case tests"""
    cmd = "pytest test_broken_link_checker.py::TestBrokenLinkCheckerEdgeCases -v"
    return run_command(cmd, "Running edge case tests")


def run_all_tests():
    """Run all tests with coverage"""
    cmd = "pytest test_broken_link_checker.py -v --cov=broken_link_checker --cov-report=html --cov-report=term"
    return run_command(cmd, "Running all tests with coverage")


def run_quick_tests():
    """Run quick tests (excluding slow ones)"""
    cmd = "pytest test_broken_link_checker.py -v -m 'not slow'"
    return run_command(cmd, "Running quick tests")


def run_performance_tests():
    """Run performance tests"""
    cmd = "pytest test_broken_link_checker.py::TestPerformance -v"
    return run_command(cmd, "Running performance tests")


def generate_html_report():
    """Generate HTML test report"""
    cmd = "pytest test_broken_link_checker.py --html=test_report.html --self-contained-html"
    return run_command(cmd, "Generating HTML test report")


def lint_code():
    """Run code linting"""
    print("🔍 Running code linting...")
    commands = [
        "flake8 broken_link_checker.py --max-line-length=88",
        "pylint broken_link_checker.py --score=yes",
    ]
    
    success = True
    for cmd in commands:
        if not run_command(cmd):
            success = False
    
    return success


def main():
    parser = argparse.ArgumentParser(description="Test runner for Broken Link Checker")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--edge", action="store_true", help="Run edge case tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests with coverage")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (no slow tests)")
    parser.add_argument("--html", action="store_true", help="Generate HTML test report")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n🚀 Quick start:")
        print("  python run_tests.py --install    # Install dependencies")
        print("  python run_tests.py --unit       # Run unit tests")
        print("  python run_tests.py --all        # Run all tests")
        print("  python run_tests.py --html       # Generate HTML report")
        return
    
    success = True
    
    if args.install:
        success &= install_dependencies()
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.edge:
        success &= run_edge_case_tests()
    
    if args.performance:
        success &= run_performance_tests()
    
    if args.all:
        success &= run_all_tests()
    
    if args.quick:
        success &= run_quick_tests()
    
    if args.html:
        success &= generate_html_report()
    
    if args.lint:
        success &= lint_code()
    
    if success:
        print("\n✅ All operations completed successfully!")
    else:
        print("\n❌ Some operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test script for AI Usage Tracker CLI
"""

import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_usage_tracker.cli import main

def test_init():
    """Test database initialization"""
    print("Testing database initialization...")
    sys.argv = ["ai-usage-tracker", "init"]
    main()

def test_status():
    """Test status command"""
    print("\nTesting status command...")
    sys.argv = ["ai-usage-tracker", "status"]
    main()

def test_providers():
    """Test providers command"""
    print("\nTesting providers command...")
    sys.argv = ["ai-usage-tracker", "providers"]
    main()

def test_summary():
    """Test summary command"""
    print("\nTesting summary command...")
    sys.argv = ["ai-usage-tracker", "summary"]
    main()

def test_budget_list():
    """Test budget list command"""
    print("\nTesting budget list command...")
    sys.argv = ["ai-usage-tracker", "budget", "list"]
    main()

if __name__ == "__main__":
    print("🧪 Testing AI Usage Tracker CLI")
    print("=" * 50)
    
    try:
        test_init()
        test_status()
        test_providers()
        test_summary()
        test_budget_list()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
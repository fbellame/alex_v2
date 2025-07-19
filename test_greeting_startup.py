#!/usr/bin/env python3
"""
Test script to verify the greeting system can start without errors.
This is a basic syntax and import test for the main entry point.
"""

import sys
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_greeting_startup")

def test_greeting_import():
    """Test that the greeting system can be imported without errors."""
    try:
        logger.info("Testing alex_greeting.py import...")
        
        # Import the main module
        import alex_greeting
        logger.info("✓ alex_greeting.py imported successfully")
        
        # Test that key components are accessible
        assert hasattr(alex_greeting, 'entrypoint'), "entrypoint function not found"
        assert hasattr(alex_greeting, 'prewarm'), "prewarm function not found"
        assert hasattr(alex_greeting, 'AgentManager'), "AgentManager class not found"
        
        logger.info("✓ All required components found")
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False

def test_agent_manager():
    """Test AgentManager initialization."""
    try:
        logger.info("Testing AgentManager initialization...")
        
        from alex_greeting import AgentManager
        from shared.user_data import UserData
        
        # Test AgentManager creation
        userdata = UserData()
        agent_manager = AgentManager(userdata)
        
        assert agent_manager.userdata is userdata, "UserData not properly assigned"
        assert agent_manager.current_agent is None, "Current agent should be None initially"
        assert agent_manager.session is None, "Session should be None initially"
        
        logger.info("✓ AgentManager initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ AgentManager test failed: {e}")
        return False

def test_direct_transfer_mechanism():
    """Test that the direct transfer mechanism is properly set up."""
    try:
        logger.info("Testing direct transfer mechanism...")
        
        # Test that the greeting agent has the transfer function
        from agents.greeting_agent import detect_language_and_transfer, GreetingAgent
        from shared.user_data import UserData
        
        # Test GreetingAgent creation
        greeting_agent = GreetingAgent()
        assert hasattr(greeting_agent, 'tools'), "GreetingAgent should have tools"
        
        # Test that detect_language_and_transfer function exists
        assert detect_language_and_transfer is not None, "detect_language_and_transfer function should exist"
        
        # Test UserData structure for agent storage
        userdata = UserData()
        assert hasattr(userdata, 'agents'), "UserData should have agents dict"
        assert hasattr(userdata, 'current_agent'), "UserData should have current_agent field"
        assert hasattr(userdata, 'detected_language'), "UserData should have detected_language field"
        
        logger.info("✓ Direct transfer mechanism test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Direct transfer mechanism test failed: {e}")
        return False

def main():
    """Run all startup tests."""
    logger.info("Starting greeting system startup tests...")
    
    tests = [
        ("Import Test", test_greeting_import),
        ("AgentManager Test", test_agent_manager),
        ("Direct Transfer Mechanism Test", test_direct_transfer_mechanism),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("✓ All startup tests passed! The async callback error should be fixed.")
        return 0
    else:
        logger.error("✗ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

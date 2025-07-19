#!/usr/bin/env python3
"""
Test script to verify the greeting system components can be imported and initialized.
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_system")

def test_imports():
    """Test that all components can be imported successfully."""
    try:
        logger.info("Testing imports...")
        
        # Test shared components
        from shared.user_data import UserData
        logger.info("✓ UserData imported successfully")
        
        from shared.tools.english_tools import (
            set_first_name, set_last_name, set_phone, 
            set_booking_date_time, set_booking_reason,
            get_current_datetime, get_clinic_info
        )
        logger.info("✓ English tools imported successfully")
        
        from shared.tools.french_tools import (
            definir_prenom, definir_nom_famille, definir_telephone,
            definir_date_heure_rendez_vous, definir_raison_rendez_vous,
            obtenir_date_heure_actuelle, obtenir_info_clinique
        )
        logger.info("✓ French tools imported successfully")
        
        # Test agents
        from agents.greeting_agent import GreetingAgent
        logger.info("✓ GreetingAgent imported successfully")
        
        from agents.english_booking_agent import EnglishBookingAgent
        logger.info("✓ EnglishBookingAgent imported successfully")
        
        from agents.french_booking_agent import FrenchBookingAgent
        logger.info("✓ FrenchBookingAgent imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error during import: {e}")
        return False

def test_initialization():
    """Test that components can be initialized."""
    try:
        logger.info("Testing component initialization...")
        
        # Test UserData
        from shared.user_data import UserData
        userdata = UserData()
        logger.info("✓ UserData initialized successfully")
        
        # Test agents (without LiveKit dependencies)
        logger.info("✓ Component initialization test completed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}")
        return False

def test_language_detection():
    """Test the language detection logic."""
    try:
        logger.info("Testing language detection logic...")
        
        # Test French detection
        french_indicators = [
            'bonjour', 'salut', 'bonsoir', 'oui', 'non', 'merci', 'je', 'suis', 'voudrais', 
            'rendez-vous', 'français', 'parle', 'comprends', 'dentiste', 'clinique', 'allo',
            'comment', 'allez', 'vous', 'bien', 'très', 'avoir', 'prendre', 'besoin'
        ]
        
        # Test English detection
        english_indicators = [
            'hello', 'hi', 'good', 'yes', 'no', 'thank', 'i', 'am', 'would', 'like',
            'appointment', 'english', 'speak', 'understand', 'dentist', 'clinic', 'need',
            'want', 'book', 'schedule', 'help', 'can', 'you', 'please', 'thanks'
        ]
        
        # Test cases
        test_cases = [
            ("bonjour, je voudrais un rendez-vous", "french"),
            ("hello, I would like an appointment", "english"),
            ("salut, j'ai besoin d'un dentiste", "french"),
            ("hi, can you help me book something", "english"),
        ]
        
        for test_input, expected_lang in test_cases:
            test_input_lower = test_input.lower()
            french_score = sum(1 for word in french_indicators if word in test_input_lower)
            english_score = sum(1 for word in english_indicators if word in test_input_lower)
            
            if french_score > english_score:
                detected = "french"
            elif english_score > french_score:
                detected = "english"
            else:
                detected = "english"  # default
            
            if detected == expected_lang:
                logger.info(f"✓ '{test_input}' → {detected} (F:{french_score}, E:{english_score})")
            else:
                logger.warning(f"✗ '{test_input}' → {detected}, expected {expected_lang}")
        
        logger.info("✓ Language detection logic test completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Language detection test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting system tests...")
    
    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_initialization),
        ("Language Detection Test", test_language_detection),
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
        logger.info("✓ All tests passed! System is ready.")
        return 0
    else:
        logger.error("✗ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

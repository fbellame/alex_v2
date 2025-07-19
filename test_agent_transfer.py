"""
Test script to verify agent transfer functionality works without runtime errors
"""
import asyncio
import logging
from unittest.mock import Mock, AsyncMock
from shared.user_data import UserData
from agents.greeting_agent import detect_language_and_transfer
from agents.french_booking_agent import FrenchBookingAgent
from agents.english_booking_agent import EnglishBookingAgent
from livekit.agents import RunContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_agent_transfer")

async def test_french_transfer():
    """Test transferring to French agent"""
    print("Testing French agent transfer...")
    
    # Create mock userdata and agents
    userdata = UserData()
    userdata.agents = {
        "french_booking_agent": FrenchBookingAgent(),
        "english_booking_agent": EnglishBookingAgent(),
    }
    
    # Create mock session and context
    mock_session = Mock()
    mock_context = Mock(spec=RunContext)
    mock_context.userdata = userdata
    mock_context.session = mock_session
    
    # Test French language detection
    french_response = "Bonjour, je voudrais prendre un rendez-vous"
    
    try:
        result = await detect_language_and_transfer(french_response, mock_context)
        print(f"✅ French transfer successful: {result}")
        print(f"✅ Language detected: {userdata.detected_language}")
        print(f"✅ Current agent: {userdata.current_agent}")
        assert userdata.detected_language == "french"
        assert userdata.current_agent == "french_booking_agent"
        return True
    except Exception as e:
        print(f"❌ French transfer failed: {e}")
        return False

async def test_english_transfer():
    """Test transferring to English agent"""
    print("\nTesting English agent transfer...")
    
    # Create mock userdata and agents
    userdata = UserData()
    userdata.agents = {
        "french_booking_agent": FrenchBookingAgent(),
        "english_booking_agent": EnglishBookingAgent(),
    }
    
    # Create mock session and context
    mock_session = Mock()
    mock_context = Mock(spec=RunContext)
    mock_context.userdata = userdata
    mock_context.session = mock_session
    
    # Test English language detection
    english_response = "Hello, I would like to book an appointment"
    
    try:
        result = await detect_language_and_transfer(english_response, mock_context)
        print(f"✅ English transfer successful: {result}")
        print(f"✅ Language detected: {userdata.detected_language}")
        print(f"✅ Current agent: {userdata.current_agent}")
        assert userdata.detected_language == "english"
        assert userdata.current_agent == "english_booking_agent"
        return True
    except Exception as e:
        print(f"❌ English transfer failed: {e}")
        return False

async def main():
    """Run all transfer tests"""
    print("🧪 Testing Agent Transfer Functionality\n")
    
    french_success = await test_french_transfer()
    english_success = await test_english_transfer()
    
    print(f"\n📊 Test Results:")
    print(f"French Transfer: {'✅ PASS' if french_success else '❌ FAIL'}")
    print(f"English Transfer: {'✅ PASS' if english_success else '❌ FAIL'}")
    
    if french_success and english_success:
        print(f"\n🎉 All tests passed! Agent transfer fix is working correctly.")
        return True
    else:
        print(f"\n💥 Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

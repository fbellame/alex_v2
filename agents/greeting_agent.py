from livekit.agents import Agent, function_tool, RunContext
from livekit.plugins import openai
from typing import Annotated
from pydantic import Field
import logging
from shared.user_data import UserData

logger = logging.getLogger("greeting_agent")

RunContext_T = RunContext[UserData]

@function_tool()
async def detect_language_and_transfer(
    user_response: Annotated[str, Field(description="The user's response to analyze for language detection")],
    context: RunContext_T,
) -> str:
    """Detect the language of the user's response and transfer to appropriate agent."""
    userdata = context.userdata
    
    # Simple language detection logic
    user_response_lower = user_response.lower()
    
    # French indicators
    french_indicators = [
        'bonjour', 'salut', 'bonsoir', 'oui', 'non', 'merci', 'je', 'suis', 'voudrais', 
        'rendez-vous', 'français', 'parle', 'comprends', 'dentiste', 'clinique', 'allo',
        'comment', 'allez', 'vous', 'bien', 'très', 'avoir', 'prendre', 'besoin'
    ]
    
    # English indicators  
    english_indicators = [
        'hello', 'hi', 'good', 'yes', 'no', 'thank', 'i', 'am', 'would', 'like',
        'appointment', 'english', 'speak', 'understand', 'dentist', 'clinic', 'need',
        'want', 'book', 'schedule', 'help', 'can', 'you', 'please', 'thanks'
    ]
    
    french_score = sum(1 for word in french_indicators if word in user_response_lower)
    english_score = sum(1 for word in english_indicators if word in user_response_lower)
    
    # Determine language preference
    if french_score > english_score:
        detected_language = "french"
    elif english_score > french_score:
        detected_language = "english"
    else:
        # Default to English if unclear
        detected_language = "english"
    
    userdata.detected_language = detected_language
    logger.info(f"Language detected: {detected_language} (French: {french_score}, English: {english_score})")
    logger.info(userdata.summarize())
    
    if detected_language == "french":
        userdata.current_agent = "french_booking_agent"
        return "TRANSFER_TO_FRENCH_AGENT"
    else:
        userdata.current_agent = "english_booking_agent"
        return "TRANSFER_TO_ENGLISH_AGENT"


class GreetingAgent(Agent):
    def __init__(self) -> None:
        GREETING_PROMPT = """
            You are the greeting agent for SmileRight Dental Clinic.
            
            Your role is to:
            1. Greet customers with "Hi Bonjour, welcome to SmileRight Dental Clinic, how can I help you today?"
            2. Listen to their first response
            3. Use the detect_language_and_transfer function to analyze their language preference
            4. Transfer them to the appropriate specialized booking agent
            
            IMPORTANT RULES:
            - Always greet with the exact phrase: "Hi Bonjour, welcome to SmileRight Dental Clinic, how can I help you today?"
            - After the user responds, immediately call detect_language_and_transfer with their response
            - Do not engage in booking activities - your only job is language detection and transfer
            - If the function returns "TRANSFER_TO_FRENCH_AGENT", say: "Je vous transfère à notre agent de réservation en français."
            - If the function returns "TRANSFER_TO_ENGLISH_AGENT", say: "I'm transferring you to our English booking agent."
            - After the transfer message, your job is complete
        """
        
        logger.info("GreetingAgent initialized")
        
        super().__init__(
            instructions=GREETING_PROMPT,
            tools=[detect_language_and_transfer],
            tts=openai.TTS(voice="nova"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Hi Bonjour, welcome to SmileRight Dental Clinic, how can I help you today?",
            allow_interruptions=False,
        )

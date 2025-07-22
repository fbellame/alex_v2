
import logging
import os

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Annotated, Optional

import yaml
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (Agent, AgentSession,
                            JobProcess, RoomInputOptions,
                            RunContext, function_tool)
from livekit.plugins import deepgram, noise_cancellation, openai, silero
from pydantic import Field
from twilio.rest import Client
import re

load_dotenv()

logger = logging.getLogger("dental_assistant")
logger.setLevel(logging.INFO)

@dataclass
class UserData:
    customer_first_name: Optional[str] = None
    customer_last_name: Optional[str] = None
    customer_phone: Optional[str] = None
    booking_date_time: Optional[str] = None
    booking_reason: Optional[str] = None
    
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    session: Optional[AgentSession] = None
    

    def summarize(self) -> str:
        data = {
            "customer_first_name": self.customer_first_name or "unknown",
            "customer_last_name": self.customer_last_name or "unknown",
            "customer_phone": self.customer_phone or "unknown",
            "booking_date_time": self.booking_date_time or "unknown",
            "booking_reason": self.booking_reason or "unknown",
        }
        return yaml.dump(data)
    
RunContext_T = RunContext[UserData]

def format_phone_number(phone: str) -> str:
    """Format phone number to Twilio-compatible format (+12223334444)."""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone))
    
    # If the number doesn't start with 1 and has 10 digits, add 1
    if len(digits_only) == 10:
        digits_only = '1' + digits_only
    # If the number has 11 digits and starts with 1, keep as is
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        pass
    # If the number has 11 digits but doesn't start with 1, assume it's missing the country code
    elif len(digits_only) == 11 and not digits_only.startswith('1'):
        digits_only = '1' + digits_only
    
    # Add the + prefix
    return '+' + digits_only

@function_tool()
async def set_first_name(
    name: Annotated[str, Field(description="The customer's first name")],
    context: RunContext_T,
) -> str:
    """Called when the customer provides their first name."""
    userdata = context.userdata
    userdata.customer_first_name = name
    
    # Log the updated first name
    logger.info(userdata.summarize())
        
    return f"The first name is updated to {name}"

@function_tool()
async def set_last_name(
    name: Annotated[str, Field(description="The customer's last name")],
    context: RunContext_T,
) -> str:
    """Called when the customer provides their last name."""
    userdata = context.userdata
    userdata.customer_last_name = name
    
    # Log the updated last name
    logger.info(userdata.summarize())
        
    return f"The last name is updated to {name}"

@function_tool()
async def verify_phone_last_four_digits(context: RunContext_T) -> str:
    """Verify the customer's phone number by showing the last 4 digits."""
    userdata = context.userdata
    
    if userdata.customer_phone:
        # Get the last 4 digits for verification
        phone_digits = ''.join(filter(str.isdigit, userdata.customer_phone))
        if len(phone_digits) >= 4:
            last_four = phone_digits[-4:]
        else:
            last_four = "0000"
        
        logger.info(f"Verifying phone number ending in: {last_four}")
        return f"I have your phone number ending in {last_four}. Is this correct for sending the confirmation SMS?"
    else:
        return "I don't have your phone number. Could you please provide it digit by digit?"

@function_tool()
async def confirm_phone_verification(
    confirmed: Annotated[bool, Field(description="Whether the caller confirms the phone number ending digits are correct")],
    context: RunContext_T,
) -> str:
    """Called when the customer confirms or denies the phone number verification."""
    userdata = context.userdata
    
    if confirmed:
        logger.info(f"Phone number verified: {userdata.customer_phone}")
        return f"Thank you! Your phone number {userdata.customer_phone} has been verified for SMS confirmation."
    else:
        # Clear the existing phone number and ask for manual input
        userdata.customer_phone = None
        return "I understand. Please provide your correct phone number digit by digit in the format (1) 111 222 3333."

@function_tool()
async def set_phone(
    phone: Annotated[str, Field(description="The customer's phone number")],
    context: RunContext_T,
) -> str:
    """Called when the customer provides their phone number."""
    userdata = context.userdata
    
    # Format phone number to Twilio-compatible format
    formatted_phone = format_phone_number(phone)
    userdata.customer_phone = formatted_phone
    
    # Log the updated phone number
    logger.info(userdata.summarize())

    return f"The phone number is updated to {formatted_phone}"

@function_tool()
async def set_booking_date_time(
    date_time: Annotated[str, Field(description="The customer's booking date and time")],
    context: RunContext_T
) -> str:
    """Called when the customer provides their booking date and time."""
    userdata = context.userdata
    logger.info("date_time: %s", date_time)
    userdata.booking_date_time = date_time
    
    # Log the updated booking date and time
    logger.info(userdata.summarize())

    return f"The booking date and time is updated to {date_time}"

@function_tool()
async def get_current_datetime(context: RunContext_T) -> str:
    """Get the current date and time."""
    current_time = datetime.now(timezone.utc)
    # Convert to Montreal timezone (EST/EDT)
    montreal_time = current_time.astimezone()
    return f"Current date and time: {montreal_time.strftime('%A, %B %d, %Y at %I:%M %p')}"

# Clinic information constant
CLINIC_INFO = (
    "SmileRight Dental Clinic is located at 5561 St-Denis Street, Montreal, Canada. "
    "Our opening hours are Monday to Friday from 8:00 AM to 12:00 PM and 1:00 PM to 6:00 PM. "
    "We are closed on weekends."
)

@function_tool()
async def get_clinic_info(context: RunContext_T) -> str:
    """Get dental clinic location and opening hours information."""
    return CLINIC_INFO

@function_tool()
async def set_booking_reason(
    reason: Annotated[str, Field(description="The booking reason")],
    context: RunContext_T
) -> str:
    """Called when the user provides their booking reason."""
    userdata = context.userdata
    userdata.booking_reason = reason
    # Log the updated booking reason 
    logger.info(userdata.summarize())
    
    return f"The booking reason is updated to {reason}"

@function_tool()
async def send_confirmation_sms(context: RunContext_T) -> str:
    """Send SMS confirmation to the customer with all booking details."""
    userdata = context.userdata
    
    try:
        # Get Twilio credentials from environment
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([account_sid, auth_token, twilio_number]):
            logger.error("Missing Twilio credentials in environment variables")
            return "Failed to send confirmation SMS - missing credentials"
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Use the already formatted phone number from userdata
        customer_phone = userdata.customer_phone
        
        # Create confirmation message
        message_body = f"""SmileRight Dental Clinic - Appointment Confirmation
Date: {userdata.booking_date_time}
Phone: {userdata.customer_phone}
Reason: {userdata.booking_reason}
"""
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=customer_phone
        )
        
        logger.info(f"Confirmation SMS sent successfully. SID: {message.sid}")
        logger.info(f"SMS sent to: {customer_phone}")
        
        return f"Confirmation SMS sent successfully to {customer_phone}"
        
    except Exception as e:
        logger.error(f"Error sending confirmation SMS: {e}")
        return f"Failed to send confirmation SMS: {str(e)}"

@function_tool()
async def check_booking_complete(context: RunContext_T) -> str:
    """Check if all booking information has been collected and send confirmation SMS."""
    userdata = context.userdata
    
    required_fields = [
        userdata.customer_first_name,
        userdata.customer_last_name,
        userdata.customer_phone,
        userdata.booking_date_time,
        userdata.booking_reason
    ]
    
    if all(field is not None and field.strip() != "" for field in required_fields):
        logger.info("Booking complete - all information collected")
        
        # Send confirmation SMS
        sms_result = await send_confirmation_sms(context)
        logger.info(f"SMS confirmation result: {sms_result}")
        
        return "Booking is complete. All required information has been collected and confirmation SMS has been sent. Please end the call now."
    else:
        missing_fields = []
        if not userdata.customer_first_name:
            missing_fields.append("first name")
        if not userdata.customer_last_name:
            missing_fields.append("last name")
        if not userdata.customer_phone:
            missing_fields.append("phone number")
        if not userdata.booking_date_time:
            missing_fields.append("appointment date/time")
        if not userdata.booking_reason:
            missing_fields.append("reason for visit")
        
        return f"Booking incomplete. Missing: {', '.join(missing_fields)}"

@function_tool()
async def end_call(context: RunContext_T) -> str:
    """End the call after booking is complete."""
    logger.info("Ending call - booking completed")
    
    try:
        # Get the session from userdata
        session = context.userdata.session
        if session:
            await session.aclose()
            logger.info("Session closed successfully via userdata.session")
        else:
            logger.warning("No session found in userdata to close")
            
    except Exception as e:
        logger.error(f"Error ending call: {e}")
    
    return "Call ended successfully"


class MainAgent(Agent):
    def __init__(self) -> None:
        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        
        OPERATING_HOURS = "Monday to Friday from 8:00 AM to 12:00 PM and 1:00 PM to 6:00 PM"
        
        MAIN_PROMPT = f"""
            You are the automated booking agent for SmileRight Dental Clinic.
            Current date and time: {current_time}
            {CLINIC_INFO}

            LANGUAGE POLICY
            Do not switch languages once the conversation has started, even if the patient does.
            Never use special characters such as %, $, #, or *.
            
            PHONE NUMBER RULE
            The phone number is automatically initialized from the room name when the call starts.
            If a phone number is already available in the system, use verify_phone_last_four_digits function to show the last 4 digits and ask for verification.
            If the caller confirms using confirm_phone_verification function, the number is verified for SMS confirmation.
            If the caller denies or if no phone number is available, request the telephone number digit by digit using set_phone function.
            The required format is (1) 111 222 3333.
            The country code "(1)" may be omitted by the patient; if missing, add it yourself.
            Always speak or repeat the number digit by digit.
            Example: (1) 5 1 4 5 8 5 9 6 9 1.            

            BOOKING FLOW (ask only one question at a time)

            Ask for the desired appointment date and time.
            Validate that the chosen slot falls within operating hours ({OPERATING_HOURS}).
            If it does not, politely suggest the nearest available slot.

            Ask for the patient's first name.

            Ask for the patient's last name and request that they spell it letter by letter.

            For the telephone number:
            1. If a phone number is already available, use verify_phone_last_four_digits to show the last 4 digits
            2. Ask for confirmation using confirm_phone_verification function
            3. If confirmed, proceed to next step
            4. If not confirmed or no phone number available, ask for the number digit by digit using set_phone

            Ask for the reason for the visit.

            Confirm all captured details: date, time, full name, phone number, and reason.
            After confirming all details, check if the booking is complete using the check_booking_complete function.
            If the booking is complete, provide a brief closing remark such as: "We look forward to seeing you!"
            Then immediately end the call using the end_call function.

            GENERAL GUIDELINES
            Never ask two questions at once.
            Respond in clear, complete sentences.
            If the user provides unexpected information, politely steer them back to the required step.
            If the user asks for anything outside your scope (for example medical advice), respond succinctly that you can only help with booking appointments.
            If the user requests general information about the clinic such as opening hours, address, or available services, provide the requested information in the language used for the conversation."""
            
        logger.info("MainAgent initialized with prompt: %s", MAIN_PROMPT)
       
        super().__init__(
            instructions=MAIN_PROMPT,
            tools=[set_first_name, set_last_name, verify_phone_last_four_digits, set_phone, set_booking_date_time, set_booking_reason, get_current_datetime, get_clinic_info, check_booking_complete, send_confirmation_sms, end_call],
            tts=openai.TTS(voice="nova"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Hi, welcome to SmileRight Dental Clinic, how can I help you today?",
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    
def extract_phone_from_room_name(room_name: str) -> str:
    """
    Extract phone number from room name like 'call-_+15145859691_yZ35TYo5aNjy'
    Returns the phone number or None if not found
    """
    pattern = r'call-_(\+\d+)_'
    match = re.search(pattern, room_name)
    
    if match:
        return match.group(1)
    
    return None
    
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
   # Get room info and extract phone number
    room = ctx.room
    room_name = room.name
    phone_number = extract_phone_from_room_name(room_name)
    
    logger.info(f"Room name: {room_name}")
    logger.info(f"Phone number: {phone_number}")
        
    userdata = UserData()
    userdata.customer_phone = phone_number if phone_number else None
    
    userdata.agents.update({
        "main_agent": MainAgent(),
    })
    
    # Use optimized session class
    session = AgentSession(
        userdata=userdata,
        stt=deepgram.STT(model="nova-3", language="multi", ),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
        vad=silero.VAD.load(),
        max_tool_steps=5,
    )
    
    # Store session reference in userdata for access in function tools
    userdata.session = session
    
    await session.start(
        agent=userdata.agents["main_agent"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name="alex-telephony-agent"))

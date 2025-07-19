from typing import Any
from dotenv import load_dotenv
import logging
from dataclasses import dataclass, field
from typing import Annotated, Optional
from pydantic import Field
import time
import yaml
import asyncio
import argparse
import sys
from datetime import datetime, timezone

from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext, metrics, JobContext, JobProcess, UserStateChangedEvent, AgentStateChangedEvent
from livekit.plugins import (
    openai,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.voice import MetricsCollectedEvent
import logging

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
async def set_phone(
    phone: Annotated[str, Field(description="The customer's phone number")],
    context: RunContext_T,
) -> str:
    """Called when the customer provides their phone number."""
    userdata = context.userdata
    userdata.customer_phone = phone
    
    # Log the updated phone number
    logger.info(userdata.summarize())

    return f"The phone number is updated to {phone}"

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

class MainAgent(Agent):
    def __init__(self) -> None:
        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        
        super().__init__(
            instructions=
            f"You are a booking agent at SmileRight Dental Clinic. Current date and time: {current_time} "
            f"{CLINIC_INFO} "
            "Your jobs are to ask for the booking date and time (within our operating hours), then customer's first name and last name, "
            "phone number and the reason for the booking. Then confirm the reservation details with the customer. "
            "When you are asking for the last name, ask for spelling it letter by letter. "
            "NEVER ASK two questions at once. "
            "Always check that requested appointment times fall within our operating hours. "
            "Speak in clear, complete sentences with no special characters.",
            tools=[set_first_name, set_last_name, set_phone, set_booking_date_time, set_booking_reason, get_current_datetime, get_clinic_info],
            tts=openai.TTS(voice="nova"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Hi, bonjour, welcome to SmileRight Dental Clinic, how can I help you today?",
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    
    userdata = UserData()
    
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
        turn_detection=MultilingualModel(),
        max_tool_steps=5,
    )
    
    await session.start(
        agent=userdata.agents["main_agent"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

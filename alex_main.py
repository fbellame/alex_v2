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


load_dotenv()

@dataclass
class UserData:
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    booking_date_time: Optional[str] = None
    booking_reason: Optional[str] = None
    
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    

    def summarize(self) -> str:
        data = {
            "customer_name": self.customer_name or "unknown",
            "customer_phone": self.customer_phone or "unknown",
            "booking_date_time": self.booking_date_time or "unknown",
            "booking_reason": self.booking_reason or "unknown",
        }
        return yaml.dump(data)
    
RunContext_T = RunContext[UserData]

class MainAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=
            "You are a booking agent at SmileRight Dental Clinic located at 5561 St-Denis Street, Montreal, Canada. "
            "Our clinic hours are Monday to Friday from 8:00 AM to 12:00 PM and 1:00 PM to 6:00 PM. We are closed on weekends. "
            "Your jobs are to ask for the booking date and time (within our operating hours), then customer's name, "
            "phone number and the reason for the booking. Then confirm the reservation details with the customer. "
            "Always check that requested appointment times fall within our operating hours. "
            "Speak in clear, complete sentences with no special characters.",
            tools=[],
            tts=openai.TTS(voice="ash"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Hi, bonjour, welcome to SmileRight Dental Clinic, how can I help you today?",
            allow_interruptions=False,
        )

    @function_tool()
    async def confirm_reservation(self, context: RunContext_T) -> str | tuple[Agent, str]:
        """Called when the user confirms the reservation."""
        userdata = context.userdata
                
        if not userdata.customer_name or not userdata.customer_phone:
            return "Please provide your name and phone number first."

        if not userdata.booking_date_time:
            return "Please provide reservation time first."

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

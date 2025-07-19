from typing import Any
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone
import asyncio

from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext, JobProcess, function_tool, RunContext
from livekit.plugins import (
    openai,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import our custom components
from shared.user_data import UserData
from agents.greeting_agent import GreetingAgent
from agents.english_booking_agent import EnglishBookingAgent
from agents.french_booking_agent import FrenchBookingAgent

load_dotenv()

logger = logging.getLogger("alex_greeting_system")
logger.setLevel(logging.DEBUG)

def prewarm(proc: JobProcess):
    """Prewarm function to load VAD model"""
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the greeting system"""
    await ctx.connect()
    
    # Initialize user data
    userdata = UserData()
    
    # Create all agents
    userdata.agents.update({
        "greeting_agent": GreetingAgent(),
        "english_booking_agent": EnglishBookingAgent(), 
        "french_booking_agent": FrenchBookingAgent(),
    })
    
    # Create optimized session
    session = AgentSession(
        userdata=userdata,
        stt=deepgram.STT(model="nova-2", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        max_tool_steps=5,
    )
    
    # Start with greeting agent
    userdata.current_agent = "greeting_agent"
    
    await session.start(
        agent=userdata.agents["greeting_agent"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

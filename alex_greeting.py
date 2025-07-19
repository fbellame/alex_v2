from typing import Any
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone
import asyncio

from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext, JobProcess
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
logger.setLevel(logging.INFO)

class AgentManager:
    """Manages agent transitions and state"""
    
    def __init__(self, session: AgentSession, userdata: UserData):
        self.session = session
        self.userdata = userdata
        self.current_agent = None
        
    async def transfer_to_agent(self, agent_name: str):
        """Transfer to a specific agent"""
        if agent_name in self.userdata.agents:
            target_agent = self.userdata.agents[agent_name]
            
            # Update userdata
            self.userdata.prev_agent = self.current_agent
            self.current_agent = target_agent
            self.userdata.current_agent = agent_name
            
            logger.info(f"Transferring to {agent_name}")
            logger.info(self.userdata.summarize())
            
            # Perform the agent transfer
            await self.session.transfer_agent(target_agent)
            
        else:
            logger.error(f"Agent {agent_name} not found in available agents")

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
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        max_tool_steps=5,
    )
    
    # Create agent manager for handling transfers
    agent_manager = AgentManager(session, userdata)
    
    # Set up event handlers for agent transfers
    @session.on("agent_speech_committed")
    async def on_agent_speech_committed(message):
        """Handle agent transfers based on speech content"""
        if "TRANSFER_TO_FRENCH_AGENT" in str(message):
            await agent_manager.transfer_to_agent("french_booking_agent")
        elif "TRANSFER_TO_ENGLISH_AGENT" in str(message):
            await agent_manager.transfer_to_agent("english_booking_agent")
    
    # Start with greeting agent
    userdata.current_agent = "greeting_agent"
    agent_manager.current_agent = userdata.agents["greeting_agent"]
    
    await session.start(
        agent=userdata.agents["greeting_agent"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

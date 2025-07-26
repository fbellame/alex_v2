
import logging
import os

from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from livekit import agents
from livekit import api, rtc
from livekit.agents import (Agent, AgentSession,
                            JobProcess, RoomInputOptions,
                            RunContext, function_tool)
from livekit.plugins import deepgram, noise_cancellation, openai, silero
from livekit.agents import get_job_context
from pydantic import Field
from twilio.rest import Client
import re

from user_data import UserData
from recording import start_s3_recording

load_dotenv()

logger = logging.getLogger("futures_survey_assistant")
logger.setLevel(logging.INFO)
    
RunContext_T = RunContext[UserData]

class MainAgent(Agent):
    def __init__(self) -> None:
        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        
        MAIN_PROMPT = f"""
You are the automated survey agent for the InnoVet-AMR initiative on climate change, antimicrobial resistance (AMR), and animal health.
Current date and time: {current_time}

LANGUAGE POLICY
Detect the participant’s first reply.
Do not switch languages once the conversation has started, even if the participant does.
Never use special characters such as %, $, #, or *.

SURVEY FLOW (ask only one question at a time)

1) Briefly explain purpose:
   “Thank you for taking part in our InnoVet-AMR survey. We are collecting insights on trends and the changing landscape of climate change, AMR, and animal health.”

2) Question 1:
   “What are your top three trends that are driving change in this space?”

3) Question 2:
   “What are some of the biggest challenges and issues you are experiencing?”

4) Question 3:
   “What new opportunities do you see to leverage innovation?”

5) Recap:
   Summarize the participant’s three answers succinctly.

6) Completion check:
   After the recap, call check_survey_complete to ensure all three questions were answered.

7) Closing:
   If complete, say:
   “Thank you for completing this survey. We value your input and look forward to you participating in our other research.”
   Then immediately end the call using the end_call function.

GENERAL GUIDELINES
Ask only one question at a time.
Respond in clear, complete sentences.
If the participant provides unexpected information, politely steer them back to the current question.
Do not provide medical or technical advice; clarify that your role is limited to conducting this survey.
If the participant asks for information outside your scope, respond succinctly that you can only administer the survey.
"""
            
        logger.info("MainAgent initialized with prompt: %s", MAIN_PROMPT)
       
        super().__init__(
            instructions=MAIN_PROMPT,
            tools=[],
            tts=openai.TTS(voice="nova"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Hello, welcome to our survey.",
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    

# Add this function definition anywhere
async def hangup_call():
    ctx = get_job_context()
    if ctx is None:
        # Not running in a job context
        return
    
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(
            room=ctx.room.name,
        )
    )
    
async def entrypoint(ctx: agents.JobContext):
    
        
    userdata = UserData()
    
    userdata.agents.update({
        "main_agent": MainAgent(),
    })
    
    recording_success = await start_s3_recording("futures_survey", userdata)
    if recording_success:
        logger.info("S3 Recording started successfully")
    else:
        logger.warning("S3 Recording failed, continuing without recording")    
    await ctx.connect()
    
    
    # Use optimized session class
    session = AgentSession(
        userdata=userdata,
        stt=deepgram.STT(model="nova-3", language="en-US"),
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

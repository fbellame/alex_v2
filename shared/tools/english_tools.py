from typing import Annotated
from pydantic import Field
from livekit.agents import function_tool, RunContext
from datetime import datetime, timezone
import logging
from shared.user_data import UserData

logger = logging.getLogger("dental_assistant")

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

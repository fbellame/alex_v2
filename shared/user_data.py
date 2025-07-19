from dataclasses import dataclass, field
from typing import Optional
import yaml
from livekit.agents import Agent

@dataclass
class UserData:
    # Customer information
    customer_first_name: Optional[str] = None
    customer_last_name: Optional[str] = None
    customer_phone: Optional[str] = None
    booking_date_time: Optional[str] = None
    booking_reason: Optional[str] = None
    
    # Language preference
    detected_language: Optional[str] = None  # 'english' or 'french'
    
    # Agent management
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    current_agent: Optional[str] = None
    
    def summarize(self) -> str:
        data = {
            "customer_first_name": self.customer_first_name or "unknown",
            "customer_last_name": self.customer_last_name or "unknown", 
            "customer_phone": self.customer_phone or "unknown",
            "booking_date_time": self.booking_date_time or "unknown",
            "booking_reason": self.booking_reason or "unknown",
            "detected_language": self.detected_language or "unknown",
            "current_agent": self.current_agent or "unknown",
        }
        return yaml.dump(data)

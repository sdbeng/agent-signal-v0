# generate the schema for the agent request
from pydantic import BaseModel, Field
from typing import Optional

class AgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, description="User's input prompt for the agent")
    session_id: Optional[str] = Field(None, description="Thread ID for the conversation, used for state management. for memory continuity across interactions. If not provided, a new session will be created.")

class AgentResponse(BaseModel):
    session_id: str
    response: str
    safety_flagged: bool = Field(..., description="Indicates if the input was flagged for safety concerns")
    safety_reason: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    model: str
    tools_available: list[str]


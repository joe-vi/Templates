from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.enums.greeting_enum import GreetingStatus


class GreetingCreateRequest(BaseModel):
    """Request model for creating a greeting."""

    message: str = Field(..., min_length=1, max_length=500, description="Greeting message")
    status: GreetingStatus = Field(default=GreetingStatus.ACTIVE, description="Greeting status")


class GreetingResponse(BaseModel):
    """Response model for greeting."""

    id: int
    message: str
    status: GreetingStatus
    created_at: datetime

    class Config:
        from_attributes = True


class HelloWorldResponse(BaseModel):
    """Response model for hello world."""

    message: str
    timestamp: datetime

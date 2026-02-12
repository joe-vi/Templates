from datetime import datetime

from pydantic import BaseModel, Field


class GreetingCreateRequest(BaseModel):
    """Request model for creating a greeting."""

    message: str = Field(..., min_length=1, max_length=500, description="Greeting message")


class GreetingResponse(BaseModel):
    """Response model for greeting."""

    id: int
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class HelloWorldResponse(BaseModel):
    """Response model for hello world."""

    message: str
    timestamp: datetime

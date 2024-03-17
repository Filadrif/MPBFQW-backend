from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateMessage(BaseModel):
    title: str = Field(max_length=64)
    content: str


class UpdateMessage(BaseModel):
    title: Optional[str] = Field(max_length=64)
    content: Optional[str]


class MessageAttachment(BaseModel):
    id: int
    title: str


class GetMessage(BaseModel):
    title: str 
    content: str
    last_activity_at: datetime
    owner_name: str
    attachments: List[MessageAttachment]


class GetAllCourseMessages(BaseModel):
    message_id: int
    title: str
    content: str
    last_activity_at: datetime
    owner_name: str


class MessageCreatedData(BaseModel):
    message_id: int

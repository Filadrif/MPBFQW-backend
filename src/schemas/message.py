from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateMessage(BaseModel):
    title: str = Field(max_length=64)
    content: dict


class UpdateMessage(BaseModel):
    title: Optional[str] = Field(max_length=64)
    content: Optional[dict]


class MessageAttachment(BaseModel):
    id: int
    file_name: str
    s3_path: str


class GetMessage(BaseModel):
    title: str 
    content: dict
    last_activity_at: datetime
    owner_name: str
    attachments: List[MessageAttachment]


class GetAllCourseMessages(BaseModel):
    message_id: int
    title: str
    content: dict
    last_activity_at: datetime
    owner_name: str


class MessageCreatedData(BaseModel):
    message_id: int


class GetAllCourseAttachments(BaseModel):
    id: int
    title: str
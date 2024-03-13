from pydantic import BaseModel, Field
from typing import Optional, List


class GetCourseMinimal(BaseModel):
    id: int
    name: str
    description: str
    owner_name: str
    total_duration: int = Field(description="Show total duration of all sections")
    sections: int = Field(description="Show number of sections in course")


class GetCourseRecent(BaseModel):
    id: int
    name: str
    owner_name: str


class GetCourse(BaseModel):
    name: str
    description: str
    course_tags: List[str]
    owner_name: str


class CourseCreate(BaseModel):
    name: str
    description: str
    course_tags: List[str]


class CourseUpdate(BaseModel):
    id: int
    name: str
    description: str = Field(max_length=512)
    course_tags: List[str]
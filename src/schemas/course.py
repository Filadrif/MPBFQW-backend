from pydantic import BaseModel, Field
from typing import Optional, List


class GetAllCourses(BaseModel):
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
    description: str = Field(max_length=512)
    course_tags: List[str]


class CourseSectionCreate(BaseModel):
    name: str = Field(max_length=64)
    duration: int = Field(description="Shows duration of course section. Should be greater than 0", gt=0)


class CourseSectionUpdate(BaseModel):
    section_id: int
    name: Optional[str] = Field(max_length=64)
    duration: Optional[int] = Field(description="Shows duration of course section. Should be greater than 0", gt=0)


class CourseUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str] = Field(max_length=512)
    course_tags: Optional[List[str]]


class CourseCreatedData(BaseModel):
    course_id: int


class CourseSectionCreatedData(BaseModel):
    section_id: int

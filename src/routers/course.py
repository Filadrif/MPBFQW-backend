import sqlalchemy.exc
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import load_only
from sqlalchemy.sql import func
from db import get_database, Session
from auth import get_user, get_teacher, get_admin
from models.user import Account
from models.course import Course, CourseInfo
from schemas.course import CourseCreate
import errors


router = APIRouter()


@router.post("/", response_model=int)
async def create_course(params: CourseCreate,
                        user: Account = Depends(get_teacher),
                        db: Session = Depends(get_database)):
    """Creates a new course"""
    # Check for course with new course's name
    if db.query(Course).options(load_only(Course.name)).filter_by(name=params.name).first() is not None:
        raise errors.course_name_is_not_unique()

    new_course = Course(name=params.name, owner=user.id)
    db.add(new_course)
    try:
        new_course_info = CourseInfo(description=params.description,
                                     course_tags=params.course_tags,
                                     created_at=datetime.now())
        db.add(new_course_info)
        db.commit()
    except sqlalchemy.exc.SQLAlchemyError:
        db.rollback()

    return new_course.id


@router.post("/section")
async def create_course_section():
    """Creates a new course section"""
    pass


@router.post("/lesson")
async def create_course_lesson():
    """Creates a new course section"""
    pass


@router.post("/task")
async def create_course_task():
    """Creates a new course lesson"""
    pass


@router.post("/message")
async def create_course_message():
    pass


@router.get("/{course_id}")
async def get_course(course_id: int):
    pass


@router.get("/{course_id}")
async def get_course_section():
    pass


@router.get("/{course_id}")
async def get_course_lesson():
    pass


@router.get("/{course_id}")
async def get_course_task():
    pass


@router.get("/{course_id}")
async def update_course():
    pass


@router.get("")
async def update_course_section():
    pass


@router.get("")
async def update_course_lesson():
    pass


@router.get("")
async def update_course_task():
    pass

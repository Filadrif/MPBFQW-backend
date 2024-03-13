import sqlalchemy.exc
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import load_only
from sqlalchemy.sql import func

from db import get_database, Session
from auth import get_user, get_teacher, get_admin
from models.user import Account
from models.course import Course, CourseInfo, CourseSection
from schemas.enums import EnumAccountType
from schemas.course import (CourseCreate, CourseUpdate, CourseCreatedData, GetAllCourses, CourseSectionCreate,
                            CourseSectionUpdate)

import errors


router = APIRouter()


@router.post("/", response_model=CourseCreatedData)
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

    return CourseCreatedData(id=new_course.id)


@router.post("/section/{course_id}")
async def create_course_section(course_id: int,
                                params: CourseSectionCreate,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """Creates a new course section"""
    course = db.query(Course).filter_by(id=course_id).options(load_only(Course.id)).first()
    if course is None:
        raise errors.course_not_found()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()

    section = CourseSection(
        course_id=course_id,
        name=params.name,
        duration=params.duration
    )
    db.add(course)
    db.commit()


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


@router.put("/{course_id}", status_code=204)
async def update_course(course_id: int,
                        params: CourseUpdate,
                        user: Account = Depends(get_teacher),
                        db: Session = Depends(get_database)):
    """Updates base course params"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise errors.course_not_found()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()

    if params.name is not None:
        course.name = params.name
    if params.description is not None:
        course.description = params.description
    if params.course_tags is not None:
        course.course_tags = params.course_tags

    db.commit()


@router.put("/{course_id}/section", status_code=204)
async def update_course_section(course_id: int,
                                params: CourseSectionUpdate,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """Updates section params"""
    section = (db.query(CourseSection).
               filter(CourseSection.course_id == course_id,
                      CourseSection.id == params.section_id).
               first())
    if section is None:
        raise errors.course_section_not_found()
    course = db.query(Course).options(load_only(Course.owmer)).filter_by(id=course_id).first()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()

    if params.name is not None:
        section.name = params.name
    if params.duration is not None:
        section.duration = params.duration
    db.commit()


@router.put("")
async def update_course_lesson():
    pass


@router.put("")
async def update_course_task():
    pass


@router.put("/{course_id}/publish", status_code=204)
async def update_course_publishing(course_id: int,
                                   is_published: bool = Query(),
                                   user: Account = Depends(get_teacher),
                                   db: Session = Depends(get_database)):
    """Makes course published or unpublished"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise errors.course_not_found()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()
    course.is_published = is_published
    db.commit()


@router.put("/{course_id}/section/access", status_code=204)
async def update_course_section_access(course_id: int,
                                       section_id: int = Query(),
                                       is_opened: bool = Query(),
                                       user: Account = Depends(get_teacher),
                                       db: Session = Depends(get_database)):
    """Makes course section opened or closed"""
    section = (db.query(CourseSection).
               filter(CourseSection.id == course_id,
                      CourseSection.id == section_id).
               first())
    if section is None:
        raise errors.course_section_not_found()
    course = db.query(Course).options(load_only(Course.owmer)).filter_by(id=course_id).first()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()

    section.is_opened = is_opened
    db.commit()

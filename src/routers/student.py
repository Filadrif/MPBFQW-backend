import sqlalchemy.exc
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import load_only, joinedload
from sqlalchemy.sql import func
from typing import List, Annotated
from db import get_database, Session
from auth import get_user, get_teacher, get_admin
from models.user import Account, AccountInfo
from models.course import Course, CourseInfo, CourseStatistics, CourseSection
from schemas.enums import EnumAccountType
from schemas.course import GetCourseRecent, GetAllCourses
from func.tools import get_user_full_name
import errors


router = APIRouter()


@router.post("/{course_id}/register", status_code=204,
             responses=errors.with_errors(errors.course_not_found(),
                                          errors.course_registration_already_exists()))
async def course_registration(course_id: int,
                              user: Account = Depends(get_user),
                              db: Session = Depends(get_database)):
    """Uses for student's registration on course"""
    if db.query(Course).options(load_only(Course.id)).filter_by(id=course_id, is_published=True).first() is None:
        raise errors.course_not_found()
    existing_registration = db.query(CourseStatistics).filter_by(account_id=user.id, course_id=course_id).first()
    if existing_registration is not None:
        raise errors.course_registration_already_exists()

    registration = CourseStatistics(account_id=user.id,
                                    course_id=course_id,
                                    last_action_at=datetime.now())
    db.add(registration)
    db.commit()


@router.get("/my/courses/all", response_model=List[GetAllCourses],
            responses=errors.with_errors())
async def get_all_my_courses(limit: int,
                             page: int,
                             user: Account = Depends(get_user),
                             db: Session = Depends(get_database)):
    """Shows all courses that user joined"""
    courses = (db.query(CourseStatistics).
               filter_by(account_id=user.id).
               options(load_only(CourseStatistics.course_id)).
               order_by(CourseStatistics.last_action_at.desc()).
               offset(max((page - 1) * limit, 0)).
               limit(limit).
               all())

    # Показывать закончил ли курс 
    # Под секциями подразумевается количество секций
    pass


@router.get("/courses/recent", response_model=List[GetCourseRecent])
async def get_my_recent_courses(limit: int = 3,
                                user: Account = Depends(get_user),
                                db: Session = Depends(get_database)):
    """Shows user his 3 course by last activity date"""
    courses = (db.query(CourseStatistics).
               filter_by(account_id=user.id).
               options(load_only(CourseStatistics.course_id)).
               order_by(CourseStatistics.last_action_at.desc()).
               limit(limit).
               all())

    recent_courses = []
    for course in courses:
        recent_courses.append(GetCourseRecent(id=course.id,
                                              name=course.name,
                                              owner_name=get_user_full_name(course.course.onwer)))

    return recent_courses


@router.get("/search/courses", response_model=List[GetAllCourses],
            responses=errors.with_errors())
def get_all_courses(limit: int,  # Add check for > 0
                    page: int,  # Add check for > 0
                    user: Account = Depends(get_user),
                    db: Session = Depends(get_database)):
    """Get all courses that user can join"""
    joined_courses = db.query(CourseStatistics).options(load_only(CourseStatistics.account_id, CourseStatistics.course_id)).filter_by(account_id=user.id).all()

    courses = (db.query(Course).
               filter(Course.is_published, Course.id.notin_(joined_courses)).
               order_by(Course.id.desc()).
               offset(max((page - 1) * limit, 0)).
               limit(limit).
               all())
    
    result = []
    for course in courses:
        sections = db.query(CourseSection).options(load_only(CourseSection.duration)).filter_by(course_id=course.id).first()
        result.append(GetAllCourses(id=course.id,
                                    name=course.name,
                                    description=course.description,
                                    owner_name=get_user_full_name(course.owner),
                                    total_duration=sum([section.duration for section in sections]),
                                    sections=len(sections),))

    return result


# TODO Get user's course
    
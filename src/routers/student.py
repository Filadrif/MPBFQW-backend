import sqlalchemy.exc
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import load_only, joinedload
from sqlalchemy.sql import func
from typing import List
from db import get_database, Session
from auth import get_user, get_teacher, get_admin
from models.user import Account, AccountInfo
from models.course import Course, CourseInfo, CourseStatistics
from schemas.enums import EnumAccountType
from schemas.course import GetCourseRecent, GetAllCourses
import errors


router = APIRouter()


@router.post("/{course_id}/register}", status_code=204)
async def course_registration(course_id: int,
                              user: Account = Depends(get_user),
                              db: Session = Depends(get_database)):
    """Uses for student's registration on course"""
    if db.query(Course).options(load_only(Course.id)).filter_by(id=course_id).first() is None:
        raise errors.course_not_found()
    existing_registration = db.query(CourseStatistics).filter_by(account_id=user.id, course_id=course_id).first()
    if existing_registration is not None:
        raise errors.course_registration_already_exists()

    registration = CourseStatistics(account_id=user.id,
                                    course_id=course_id,
                                    last_action=datetime.now())
    db.add(registration)
    db.commit()


@router.get("/courses/all")
async def get_all_my_courses(user: Account = Depends(get_user),
                             db: Session = Depends(get_database)):
    courses = db.query(CourseStatistics).filter_by(account_id=user.id)


@router.get("/courses/recent", response_model=List[GetCourseRecent])
async def get_my_recent_courses(user: Account = Depends(get_user),
                                db: Session = Depends(get_database)):
    """Shows user his 3 course by last activity date"""
    courses = (db.query(CourseStatistics).
               filter_by(account_id=user.id).
               options(load_only(CourseStatistics.course_id)).
               order_by(CourseStatistics.last_action_at.desc()).
               limit(3))
    courses = courses.join(Course, CourseStatistics.course_id == Course.id)
    courses = courses.join(AccountInfo, CourseStatistics.account_id == AccountInfo.account_id)
    courses = courses.all()

    recent_courses = []
    for course in courses:
        recent_courses.append(GetCourseRecent(id=course.id,
                                              name=course.name,
                                              owner_name=course.surname + course.name))

    return recent_courses


@router.get("/courses/all", response_model=List[GetAllCourses])
def get_all_courses(user: Account = Depends(get_user),
                    db: Session = Depends(get_database)):
    courses = db.query(Course).filter_by(is_opened=True)

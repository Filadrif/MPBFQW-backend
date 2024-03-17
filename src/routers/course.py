import sqlalchemy.exc
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import load_only
from sqlalchemy.sql import func
from typing import List
import traceback
import logging

from db import get_database, Session
from auth import get_user, get_teacher, get_admin
from models.user import Account
from models.course import Course, CourseInfo, CourseSection, CourseLesson, CourseTask, CourseProgress, CourseStatistics, CourseFiles
from schemas.enums import EnumAccountType
from schemas.course import (CourseCreate, CourseUpdate, CourseCreatedData, GetAllCourses, CourseSectionCreate,
                            CourseSectionUpdate, CourseSectionCreatedData, CourseLessonCreate, CourseLessonCreatedData, 
                            CourseTaskCreatedData, CourseStructure, CourseSectionStructure)
import S3.s3 as s3
import errors


router = APIRouter()


@router.post("/", response_model=CourseCreatedData,
             responses=errors.with_errors(errors.course_name_is_not_unique(),
                                          errors.database_transaction_error()))
async def create_course(params: CourseCreate,
                        user: Account = Depends(get_teacher),
                        db: Session = Depends(get_database)):
    """Creates a new course"""
    # Check for course with new course's name
    if db.query(Course).options(load_only(Course.name)).filter_by(name=params.name).first() is not None:
        raise errors.course_name_is_not_unique()

    new_course = Course(name=params.name, owner=user.id)
    db.add(new_course)
    db.flush()
    try:
        new_course_info = CourseInfo(course_id=new_course.id,
                                     description=params.description,
                                     course_tags=params.course_tags,
                                     created_at=datetime.now())
        db.add(new_course_info)
        db.commit()
    except sqlalchemy.exc.IntegrityError:
        logging.error(f"An error occurred while creating new course: {traceback.format_exc()}")
        db.rollback()
        raise errors.database_transaction_error()

    return CourseCreatedData(course_id=new_course.id)


@router.post("/section", response_model=CourseSectionCreatedData,
             responses=errors.with_errors(errors.course_not_found(),
                                          errors.access_denied()))
async def create_course_section(params: CourseSectionCreate,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """Creates a new course section"""
    course = db.query(Course).filter_by(id=params.course_id).options(load_only(Course.id)).first()
    if course is None:
        raise errors.course_not_found()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()

    section = CourseSection(
        course_id=params.course_id,
        name=params.name,
        duration=params.duration
    )
    db.add(section)
    db.commit()

    return CourseSectionCreatedData(section_id=section.id)


@router.post("/lesson", response_model=CourseLessonCreatedData, 
             responses=errors.with_errors())
async def create_course_lesson(params: CourseLessonCreate,
                               user: Account = Depends(get_teacher),
                               db: Session = Depends(get_database)):
    """Creates a new course section"""
    section = db.query(CourseSection).filter_by(id=params.section_id).first()
    if section is None:
        raise errors.lesson_not_found()
    if user.account_type == EnumAccountType.teacher and section.course.owner != user.id:
        raise errors.access_denied()
    
    lesson = CourseLesson(name=params.name,
                          section_id=params.section_id)
    db.add(lesson)
    db.commit()

    return CourseLessonCreatedData(lesson_id=lesson.id)


@router.post("/task", response_model=CourseTaskCreatedData,
             responses=errors.with_errors())
async def create_course_task(user: Account = Depends(get_teacher),
                             db: Session = Depends(get_database)):
    """Creates a new course lesson"""
    pass


@router.get("/{course_id}")
async def get_course(course_id: int):
    pass


@router.get("/{course_id}/section/{section_id}")
async def get_course_section(course_id: int, section_id: int):
    pass


@router.get("/{course_id}/lesson/{lesson_id}")
async def get_course_lesson(course_id: int, lesson_id: int):
    pass


@router.get("/{course_id}/task/task/{task_id}")
async def get_course_task(course_id: int, task_id: int):
    pass


@router.put("/{course_id}", status_code=204,
            responses=errors.with_errors(errors.course_not_found(),
                                         errors.access_denied()))
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


@router.put("/section", status_code=204,
            responses=errors.with_errors(errors.course_section_not_found(),
                                         errors.access_denied()))
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


@router.put("/lesson", status_code=204,
            responses=errors.with_errors())
async def update_course_lesson(user: Account = Depends(get_teacher),
                               db: Session = Depends(get_database)):
    pass


@router.put("/task", status_code=204, 
            responses=errors.with_errors())
async def update_course_task(user: Account = Depends(get_teacher),
                             db: Session = Depends(get_database)):
    pass


@router.put("/{course_id}/publish", status_code=204,
            responses=errors.with_errors(errors.course_not_found(),
                                         errors.access_denied()))
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


@router.put("/{course_id}/section/access", status_code=204,
            responses=errors.with_errors(errors.course_section_not_found(),
                                         errors.access_denied()))
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


@router.delete("/", status_code=204,
               responses=errors.with_errors(errors.course_not_found(),
                                            errors.access_denied(),
                                            errors.resource_not_found(),
                                            errors.action_without_force_denied()))
async def delete_course(course_id: int,
                        force: bool = Query(False),
                        db: Session = Depends(get_database),
                        user: Account = Depends(get_teacher)):
    course = db.query(Course).filter_by(id=course_id).first()
    if course is None:
        raise errors.course_not_found()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()
    sections = db.query(CourseSection).filter_by(course_id=course_id).all()
    lessons = db.query(CourseLesson).filter(CourseLesson.section_id.in_([id for id in sections.id])).all()
    tasks = db.query(CourseTask).filter(CourseTask.lesson_id.in_([id for id in lessons.id])).all()
    task_progress = db.query(CourseProgress).filter_by(course_id=course_id).all()
    course_files = db.query(CourseFiles).filter(CourseFiles.task_id.in_([id for id in task.id])).all()
    course_stats = db.query(CourseStatistics).filter_by(course_id=course_id).all()
    if len(task_progress) and not force:
        raise errors.action_without_force_denied()
    s3_session = s3.S3()
    for task_file in course_files:
        if not s3_session.has_file(task_file.s3_path):
            raise errors.resource_not_found()
        s3_session.delete_file(task_file.s3_path)
        db.delete(task_file)
    for progress in task_progress:
        db.delete(progress)
    for task in tasks:
        db.delete(task)
    for lesson in lessons:
        db.delete(lesson)
    for section in sections:
        db.delete(section)
    for stat in course_stats:
        db.delete(stat)
    db.delete(course)


@router.delete("/section/{section_id}", status_code=204,
               responses=errors.with_errors(errors.action_without_force_denied(),
                                            errors.access_denied(),
                                            errors.section_not_found(),
                                            errors.resource_not_found()))
async def delete_section(section_id: int,
                         force: bool = Query(False),
                         db: Session = Depends(get_database),
                         user: Account = Depends(get_teacher)):
    """
    Delete course section with all lessons and tasks.
    Use force to delete course with statistics
    """
    section = db.query(CourseSection).filter_by(id=section_id).first()
    if section is None:
        raise errors.section_not_found()
    if user.account_type == EnumAccountType.teacher and section.course.owner != user.id:
        raise errors.access_denied()
    
    lessons = db.query(CourseLesson).filter(section_id=section_id).all()
    tasks = db.query(CourseTask).filter(CourseTask.lesson_id.in_([id for id in lessons.id])).all()
    task_progress = db.query(CourseProgress).filter_by(course_id=section.course.id).all()
    course_files = db.query(CourseFiles).filter(CourseFiles.task_id.in_([id for id in task.id])).all()
    
    if len(task_progress) and not force:
        raise errors.action_without_force_denied()
    s3_session = s3.S3()
    for task_file in course_files:
        if not s3_session.has_file(task_file.s3_path):
            raise errors.resource_not_found()
        s3_session.delete_file(task_file.s3_path)
        db.delete(task_file)
    for progress in task_progress:
        db.delete(progress)
    for task in tasks:
        db.delete(task)
    for lesson in lessons:
        db.delete(lesson)
 
    db.delete(section)
    
    


@router.delete("/lesson/{lesson_id}", status_code=204,
               responses=errors.with_errors(errors.access_denied(),
                                            errors.action_without_force_denied(),
                                            errors.lesson_not_found(),
                                            errors.resource_not_found()))
async def delete_lesson(lesson_id: int,
                        force: bool = Query(False),
                        db: Session = Depends(get_database),
                        user: Account = Depends(get_teacher)):
    """
    Delete course lesson  with all tasks.
    Use force to delete course with statistics
    """
    lesson = db.query(CourseLesson).filter(id=lesson_id).first()
    if lesson is None:
        raise errors.lesson_not_found()
    if user.account_type == EnumAccountType.teacher and lesson.section.course.owner != user.id:
        raise errors.access_denied()
    
    tasks = db.query(CourseTask).filter_by(lesson_id=lesson_id).all()
    task_progress = db.query(CourseProgress).filter_by(course_id=lesson.section.course.owner).all()
    course_files = db.query(CourseFiles).filter(CourseFiles.task_id.in_([id for id in task.id])).all()
    
    if len(task_progress) and not force:
        raise errors.action_without_force_denied()
    s3_session = s3.S3()
    for task_file in course_files:
        if not s3_session.has_file(task_file.s3_path):
            raise errors.resource_not_found()
        s3_session.delete_file(task_file.s3_path)
        db.delete(task_file)
    for progress in task_progress:
        db.delete(progress)
    for task in tasks:
        db.delete(task)
 
    db.delete(lesson)


@router.delete("/task/{task_id}", status_code=204,
               responses=errors.with_errors(errors.action_without_force_denied(),
                                            errors.access_denied(),
                                            errors.task_not_found(),
                                            errors.resource_not_found()))
async def delete_task(task_id: int,
                      force: bool = Query(False),
                      db: Session = Depends(get_database),
                      user: Account = Depends(get_teacher)):
    """
    Delete course lesson  with all additional files.
    Use force to delete course with statistics
    """
    task = db.query(CourseTask).filter_by(id=task_id).first()
    if task is None:
        raise errors.task_not_found()
    if user.account_type == EnumAccountType.teacher and task.lesson.section.course.owner != user.id:
        raise errors.access_denied()
    task_progress = db.query(CourseProgress).filter_by(course_id=task.lesson.section.course.id).all()
    course_files = db.query(CourseFiles).filter(CourseFiles.task_id.in_([id for id in task.id])).all()
    
    if len(task_progress) and not force:
        raise errors.action_without_force_denied()
    s3_session = s3.S3()
    for task_file in course_files:
        if not s3_session.has_file(task_file.s3_path):
            raise errors.resource_not_found()
        s3_session.delete_file(task_file.s3_path)
        db.delete(task_file)
    for progress in task_progress:
        db.delete(progress)
 
    db.delete(task)


@router.delete("/task_files", status_code=204,
               responses=errors.with_errors(errors.resource_not_found()))
async def delete_task_files(task_id: int,
                            file_ids: List[int],
                            db: Session = Depends(get_database),
                            user: Account = Depends(get_teacher)):
    """Delete files connected to task"""
    task_files = db.query(CourseFiles).filter(CourseFiles.task_id == task_id,
                                              CourseFiles.id.in_(file_ids))
    if user.account_type == EnumAccountType.teacher:
        task_files.filter(CourseFiles.owner==user.id)
    task_files = task_files.all()
    s3_session = s3.S3()
    for task_file in task_files:
        if not s3_session.has_file(task_file.s3_path):
            raise errors.resource_not_found()
        s3_session.delete_file(task_file.s3_path)
        db.delete(task_file)


@router.get("/{course_id}/structure", response_model=CourseStructure,
            responses=errors.with_errors())
async def get_course_structure_info(course_id: int,
                                    db: Session = Depends(get_database),
                                    user: Account = Depends(get_user)):
    """Shows Lists of sections of lessons"""
    pass


@router.get("/lesson/{lesson_id}/structure/",
            responses=errors.with_errors())
async def get_lesson_structure_info(course_id: int,
                                    db: Session = Depends(get_database),
                                    user: Account = Depends(get_user)):
    """Shows structure of lesson"""
    pass

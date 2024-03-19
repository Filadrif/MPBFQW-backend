from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import FileResponse, Response
from typing import List
from sqlalchemy.orm import load_only
from tempfile import TemporaryDirectory

import os.path as p


from db import get_database, Session
from auth import get_user, get_teacher
from models.user import Account
from models.course import Course, CourseMessage, CourseFiles, CourseStatistics
from schemas.enums import EnumAccountType
from schemas.message import (CreateMessage, GetMessage, UpdateMessage, GetAllCourseMessages, MessageAttachment,
                             MessageCreatedData)
from func.tools import get_user_full_name

import S3.s3 as s3
import errors

router = APIRouter()


@router.post("/message", response_model=MessageCreatedData,
             responses=errors.with_errors(errors.course_not_found(),
                                          errors.access_denied()))
async def create_course_message(course_id: int,
                                params: CreateMessage,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    course = db.query(Course).filter_by(id=course_id).options(load_only(Course.id)).first()
    if course is None:
        raise errors.course_not_found()
    if user.account_type == EnumAccountType.teacher and course.owner != user.id:
        raise errors.access_denied()

    message = CourseMessage(course_id=course_id,
                            account_id=user.id,
                            content=params.content,
                            title=params.title)
    db.add(message)
    db.commit()

    return MessageCreatedData(message_id=message.id)


@router.put("/message/{message_id}", status_code=204,
            responses=errors.with_errors(errors.access_denied(),
                                         errors.course_message_not_found()
                                         ))
async def update_course_message(message_id: int,
                                params: UpdateMessage,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """Update message content or title"""
    message = db.query(CourseMessage).filter_by(id=message_id).first()
    if message is None:
        raise errors.course_message_not_found()
    if user.account_type == EnumAccountType.teacher and message.course.owner != user.id:
        raise errors.access_denied()

    if params.content is not None:
        message.content = params.content
    if params.title is not None:
        message.title = params.title
    message.updated_at = datetime.now()

    db.commit()


@router.get("/message/{message_id}", response_model=GetMessage,
            responses=errors.with_errors(errors.course_message_not_found(),
                                         errors.access_denied()))
async def get_course_message(message_id: int,
                             user: Account = Depends(get_user),
                             db: Session = Depends(get_database)):
    """Gives message data with attachments list"""
    message = db.query(CourseMessage).filter_by(id=message_id).first()
    if message is None:
        raise errors.course_message_not_found()
    if user.account_type is EnumAccountType.student and db.query(CourseStatistics).filter_by(course_id=message.course_id, account_id=user.id).first() is None:
        raise errors.access_denied()
    
    attachments = (db.query(CourseFiles).
                   options(load_only(CourseFiles.id,
                                     CourseFiles.name)).
                   filter_by(message_id=message_id).
                   all())
    attachments_list = []
    for attachment in attachments:
        attachments_list.append(MessageAttachment(
            id=attachment.id,
            title=attachment.name,
        ))

    owner_name = get_user_full_name(message.account_id)
    return GetMessage(title=message.title,
                      content=message.content,
                      owner_name=owner_name,
                      last_activity_at=message.created_at,
                      attachments=attachments_list)


@router.delete("/message/{message_id}", status_code=204,
               responses=errors.with_errors(errors.course_message_not_found(),
                                            errors.access_denied()))
async def delete_course_message(message_id: int,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """
    Delete course message 
    Note: all attachments will be also deleted
    """
    message = db.query(CourseMessage).filter_by(id=message_id).first()
    if message is None:
        raise errors.course_message_not_found()
    if user.account_type == EnumAccountType.teacher and message.course.owner != user.id:
        raise errors.access_denied()

    attachments = db.query(CourseFiles).filter_by(message_id=message_id).all()
    s3_session = s3.S3()
    for attachment in attachments:
        if s3_session.has_file(attachment.s3_path):
            s3_session.delete_file(attachment.s3_path)
        db.delete(attachment)

    db.delete(message)
    db.commit()


@router.get("/{course_id}/message/all", response_model=List[GetAllCourseMessages])
async def get_all_course_messages(course_id: int,
                                  limit: int,  # Add check for > 0
                                  page: int,  # Add check for > 0
                                  user: Account = Depends(get_user),
                                  db: Session = Depends(get_database)):
    """Get limit number of messages with base info"""
    messages = (db.query(CourseMessage).
                filter_by(course_id=course_id).
                order_by(CourseMessage.created_at.desc()).
                offset((page - 1) * limit).
                limit(limit).
                all())
    result = []
    for message in messages:
        owner_name = get_user_full_name(message.account_id)
        result.append(GetAllCourseMessages(message_id=message.id,
                                           title=message.title,
                                           content=message.content,
                                           last_activity_at=message.updated_at,
                                           owner_name=owner_name))

    return result


@router.post("/message/attachment", status_code=201,
             responses=errors.with_errors(errors.course_message_not_found(),
                                          errors.access_denied()))
async def create_message_attachment(message_id: int,
                                    file_title: str,
                                    file: UploadFile,
                                    user: Account = Depends(get_teacher),
                                    db: Session = Depends(get_database)):
    """Upload message attachment to s3"""
    message = db.query(CourseMessage).filter_by(id=message_id).first()
    if message is None:
        raise errors.course_message_not_found()

    if user.account_type == EnumAccountType.teacher and message.account_id != user.id:
        raise errors.access_denied()

    s3_session = s3.S3()
    s3_path = f"/attachments/{message.course_id}/message/{file.filename}"
    s3_session.upload_file(file.file.read(), s3_path)
    attachment = CourseFiles(message_id=message_id,
                             name=file_title,
                             s3_path=s3_path,
                             owner=user.id)
    db.add(attachment)
    db.commit()


@router.get("/message/{message_id}/attachment/all", response_model=List[MessageAttachment],
            responses=errors.with_errors(errors.course_message_not_found(),
                                         errors.access_denied()))
async def get_all_message_attachments(message_id: int,
                                      user: Account = Depends(get_user),
                                      db: Session = Depends(get_database)):
    """Shows base info about all message attachments"""
    # Check if message with attachment exists
    message = db.query(CourseMessage).filter_by(id=message_id).first()
    if message is None:
        raise errors.course_message_not_found()
    # Check if user has rights to see attachments
    if (db.query(CourseStatistics).
            options(load_only(CourseStatistics.course_id,
                              CourseStatistics.account_id)).
            filter_by(course_id=message.course_id, account_id=user.id).
            first()) and message.account_id != user.id:
        raise errors.access_denied()

    attachments = db.query(CourseFiles).options(load_only(CourseFiles.id, CourseFiles.name)).filter_by(
        message_id=message_id).all()
    result = []
    for attachment in attachments:
        result.append(MessageAttachment(id=attachment.id, title=attachment.name))

    return result


@router.delete("/message/{message_id}/attachment", status_code=204,
               responses=errors.with_errors(errors.course_message_not_found(),
                                            errors.access_denied(),
                                            errors.attachment_not_found(),
                                            errors.resource_not_found()))
async def delete_message_attachment(message_id: int,
                                    attachment_id: int = Query(),
                                    user: Account = Depends(get_teacher),
                                    db: Session = Depends(get_database)):
    """Delete attachment from message"""
    attachment = (db.query(CourseFiles).
                  options(load_only(CourseFiles.id, CourseFiles.message_id, CourseFiles.s3_path)).
                  filter_by(id=attachment_id).
                  first())
    if attachment is None:
        raise errors.attachment_not_found()
    
    message = db.query(CourseMessage).filter_by(id=message_id).first()
    if message is None:
        raise errors.course_message_not_found()
    if user.account_type == EnumAccountType.teacher and message.account_id != user.id:
        raise errors.access_denied()

    # Delete file from s3
    s3_session = s3.S3()
    if not s3_session.has_file(attachment.s3_path):
        raise errors.resource_not_found()
    s3_session.delete_file(attachment.s3_path)

    db.delete(attachment)
    db.commit()


@router.get("/message/attachment/download", 
            responses=errors.with_errors(errors.access_denied(),
                                         errors.course_message_not_found(),
                                         errors.resource_not_found()))
async def download_attachment(attachment_id: int = Query(),
                              user: Account = Depends(get_user),
                              db: Session = Depends(get_database)):
    """User for attachment download"""
    
    attachment = (db.query(CourseFiles).
                  options(load_only(CourseFiles.id, CourseFiles.message_id, CourseFiles.s3_path)).
                  filter_by(id=attachment_id).
                  first())
    if attachment is None:
        raise errors.attachment_not_found()
    
    message = db.query(CourseMessage).options(load_only(CourseMessage.course_id)).filter_by(attachment.message_id).first()
    # Check if user has rights to download attachment
    if (db.query(CourseStatistics).
            options(load_only(CourseStatistics.course_id,
                              CourseStatistics.account_id)).
            filter_by(course_id=message.course_id, account_id=user.id).
            first()) and attachment.message.account_id != user.id:
        raise errors.access_denied()

    s3_session = s3.S3()
    with TemporaryDirectory(prefix="download_") as tmp:
        file_path = p.join(tmp, f"{attachment.name}.{attachment.s3_path.split(".")[-1]}")
        with open(file_path, mode="w+b") as f:
            if not s3_session.has_file(attachment.s3_path):
                raise errors.resource_not_found()
            s3_session.download_file(f, attachment.s3_path)
            headers = {"Content-Disposition": f"attachment; filename={attachment.name}.{attachment.s3_path.split(".")[-1]}"}
            return Response(content=f.read(),
                            media_type="multipart/form-data",
                            headers=headers)

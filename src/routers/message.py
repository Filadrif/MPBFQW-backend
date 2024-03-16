from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile
from typing import List
from sqlalchemy.orm import load_only
from collections import defaultdict

import traceback
import logging

from db import get_database, Session
from auth import get_user, get_teacher
from models.user import Account, AccountInfo
from models.course import Course, CourseMessage, CourseFiles, CourseStatistics
from schemas.enums import EnumAccountType
from schemas.message import CreateMessage, GetMessage, UpdateMessage, GetAllCourseMessages, MessageAttachement, MessageCreatedData, GetAllCourseAttachments

import S3.s3 as s3
import errors


router = APIRouter()


@router.post("/{course_id}/message", response_model=MessageCreatedData,
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

    return CourseCreatedData(message_id=message.id)


@router.put("/{course_id}/message/{message_id}", status_code=204,
            responses=errors.with_errors(errors.access_denied(),
                                         errors.course_message_not_found()
                                         ))
async def update_course_message(course_id: int,
                                message_id: int,
                                params: UpdateMessage,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """Update message content or title"""
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
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


@router.get("/{course_id}/message/{message_id}", response_model=GetMessage,
            responses=errors.with_errors(errors.course_message_not_found()))
async def get_course_message(course_id: int,
                             message_id: int,
                             user: Account = Depends(get_user),
                             db: Session = Depends(get_database)):
    """Gives message data with attachments list"""
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
    if message is None:
        raise errors.course_message_not_found()
    
    attachments = db.query(CourseFiles).options(load_only(CourseFiles.id, CourseFiles.name)).filter_by(message_id=message_id).all()
    attachments_list = []
    for attachment in attachments:
        attachments_list.append(MessageAttachement(
            id=attachment.id,
            file_name=attachment.name,
        ))
 
    owner_info = db.query(AccountInfo).options(load_only(AccountInfo.name, AccountInfo.surname, AccountInfo.patronymic)).filter_by().first()
    if owner_info.patronymic is None:
        owner_name = owner_info.surname + " " + owner_info.name 
    else:
        owner_name = owner_info.surname + " " + owner_info.name + " " + owner_info.patronymic

    return GetMessage(title=message.title,
                      content=message.content,
                      owner_name=owner_name,
                      last_activity_at=message.created_at,
                      attachments=attachments_list)


@router.delete("/{course_id}/message/{message_id}", status_code=204,
               responses=errors.with_errors(errors.course_message_not_found(),
                                            errors.access_denied()))
async def delete_course_message(course_id: int,
                                message_id: int,
                                user: Account = Depends(get_teacher),
                                db: Session = Depends(get_database)):
    """
    Delete course message 
    Note: all attachments will be also deleted
    """    
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
    if message is None:
        raise errors.course_message_not_found()
    if user.account_type == EnumAccountType.teacher and message.course.owner != user.id:
        raise errors.access_denied()
    
    attachments = db.query(CourseFiles).filter_by(message_id=message_id).all()
    for attachment in attachments:
        # TODO add deletion of file from s3
        db.delete(attachment)

    db.delete(message)
    db.commit()
    


@router.get("/{course_id}/message/all", response_model=List[GetAllCourseMessages])
async def get_all_course_messages(course_id: int,
                                  limit: int,
                                  page: int,
                                  user: Account = Depends(get_user),
                                  db: Session = Depends(get_database)):
    """Get limit number of messages with base info"""
    messages = db.query(CourseMessage).filter_by(course_id=course_id).limit(limit).offset().all()  # TODO Finish pagination
    result, owner_names = [], defaultdict()
    for message in messages:
        if message.account_id not in owner_names.keys():
            owner_info = db.query(AccountInfo).options(load_only(AccountInfo.name, AccountInfo.surname, AccountInfo.patronymic)).filter_by().first()
            if owner_info.patronymic is None:
                owner_name = owner_info.surname + " " + owner_info.name 
            else:
                owner_name = owner_info.surname + " " + owner_info.name + " " + owner_info.patronymic
            owner_names[message.account_id] = owner_name
        result.append(GetAllCourseMessages(message_id=message.id,
                                           title=message.title,
                                           content=message.content,
                                           last_activity_at=message.updated_at,
                                           owner_name=owner_names[message.account_id]))

    return result


@router.post("/{course_id}/message/{message_id}/attachment", status_code=201,
             responses=errors.with_errors(errors.course_message_not_found(),
                                          errors.access_denied()))
async def create_message_attachemnt(course_id: int,
                                    message_id: int,
                                    file_title: str,
                                    file: UploadFile,
                                    user: Account = Depends(get_teacher),
                                    db: Session = Depends(get_database)):
    """Download message attachment to s3"""
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
    if message is None:
        raise errors.course_message_not_found()
    
    if user.account_type == EnumAccountType.teacher and message.account_id != user.id:
        raise errors.access_denied()
    
    s3_session = s3.s3()
    s3_session.upload_file(file.file.read(), file.filename)
    attachment = CourseFiles(message_id=message_id,
                             name=file_title,
                             s3_path=f"/attachments/{course_id}/message/{file.filename}",  #TODO check if upload link in bucket is correct
                             owner=user.id)
    db.add(attachment)
    db.commit()
    


@router.get("/{course_id}/message/{{message_id}}/attachment/all", response_model=List[GetAllCourseAttachments],
            responses=errors.with_errors(errors.course_message_not_found(),
                                         errors.access_denied()))
async def get_all_message_attachments(course_id: int,
                                      message_id: int,
                                      user: Account = Depends(get_user),
                                      db: Session = Depends(get_database)):
    """Shows base info about all message attachemnts"""
    # Check if message with attachment exists
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
    if message is None:
        raise errors.course_message_not_found()
    # Check if has rights to see attachments
    if (db.query(CourseStatistics).
        options(load_only(CourseStatistics.course_id, 
                          CourseStatistics.account_id)).
        filter_by(course_id=course_id, account_id=user.id).
        first()) and user.account_type != EnumAccountType.admin and message.account_id != user.id:
        raise errors.access_denied()
    
    attachments = db.query(CourseFiles).options(load_only(CourseFiles.id, CourseFiles.name)).filter_by(message_id=message_id).all()
    result = []
    for attachment in attachments:
        result.append(GetAllCourseAttachments(id=attachment.id, title=attachment.name))

    return result
    
    


@router.delete("/{course_id}/message/{message_id}/attachment", status_code=204,
               responses=errors.with_errors(errors.course_message_not_found(),
                                            errors.access_denied(),
                                            errors.attachment_not_found()))
async def delete_message_attachemnt(course_id: int,
                                    message_id: int,
                                    attachment_id: int = Query(),
                                    user: Account = Depends(get_teacher),
                                    db: Session = Depends(get_database)):
    # Check if message with attachment exists
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
    if message is None:
        raise errors.course_message_not_found()
    
    if user.account_type == EnumAccountType.teacher and message.account_id != user.id:
        raise errors.access_denied()
    
    attachment = (db.query(CourseFiles).
                  options(load_only(CourseFiles.id, CourseFiles.message_id, CourseFiles.s3_path)).
                  filter_by(id=attachment_id, message_id=message_id).
                  first())
    if attachment is None:
        raise errors.attachment_not_found()
    
    # TODO here should be delete from s3

    db.delete(attachment)
    db.commit()
    


@router.get("/{course_id}/message/{message_id}/attachment", 
            responses=errors.with_errors(errors.access_denied(),
                                         errors.course_message_not_found()))
async def download_attachment(course_id: int,
                              message_id: int,
                              attachment_id: int = Query(),
                              user: Account = Depends(get_user),
                              db: Session = Depends(get_database)):
    """User for attachement dowload"""
    # Check if message with attachment exists
    message = db.query(CourseMessage).filter_by(id=message_id, course_id=course_id).first()
    if message is None:
        raise errors.course_message_not_found()
    
    # Check if has rights to download attachment
    if (db.query(CourseStatistics).
        options(load_only(CourseStatistics.course_id, 
                          CourseStatistics.account_id)).
        filter_by(course_id=course_id, account_id=user.id).
        first()) and user.account_type != EnumAccountType.admin and message.account_id != user.id:
        raise errors.access_denied()
    
    attachment = (db.query(CourseFiles).
                  options(load_only(CourseFiles.id, CourseFiles.message_id, CourseFiles.s3_path)).
                  filter_by(id=attachment_id, message_id=message_id).
                  first())
    if attachment is None:
        raise errors.attachment_not_found()
    
    # TODO here should be generated s3 link and send via multipart
    
    
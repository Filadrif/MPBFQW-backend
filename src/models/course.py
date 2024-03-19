from datetime import datetime
from typing import List, Any, Dict

from sqlalchemy import ARRAY, Integer, TIMESTAMP, func, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, apply_task_type
from schemas.enums import EnumTaskType


class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)
    owner: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True, nullable=False)


class CourseInfo(Base):
    __tablename__ = "course_info"
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), primary_key=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    course_tags: Mapped[List[str]] = mapped_column(ARRAY(String, dimensions=1), default=[])
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 server_default=func.current_timestamp(),
                                                 deferred=True, deferred_group="date")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 deferred=True, deferred_group="date")

    course: Mapped["Course"] = relationship("Course", backref="course_info", uselist=False)


class CourseMessage(Base):
    __tablename__ = "course_message"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False,
                                                 server_default=func.current_timestamp(),
                                                 deferred=True, deferred_group="date")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 server_default=func.current_timestamp(),
                                                 deferred=True, deferred_group="date")
    
    course: Mapped["Course"] = relationship("Course", backref="course_messages")


class CourseSection(Base):
    __tablename__ = "course_section"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    is_opened: Mapped[bool] = mapped_column(nullable=False, default=True)

    course: Mapped["Course"] = relationship("Course", backref="section")


class CourseLesson(Base):
    __tablename__ = "course_lesson"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("course_section.id"), nullable=False, index=True)
    is_opened: Mapped[bool] = mapped_column(nullable=False, default=True)

    section: Mapped["CourseSection"] = relationship("CourseSection", backref="lesson")


class CourseTask(Base):
    __tablename__ = "course_task"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("course_lesson.id"), nullable=False, index=True)
    task_type: Mapped[EnumTaskType] = mapped_column(apply_task_type, nullable=False, index=True)
    content: Mapped[Dict[Any, Any]] = mapped_column(JSONB, nullable=True)

    lesson: Mapped["CourseLesson"] = relationship("CourseLesson", backref="task")


class CourseProgress(Base):
    __tablename__ = "course_progress"
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), primary_key=True, index=True, nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("course_task.id"), index=True, nullable=False)
    finished: Mapped[bool] = mapped_column(nullable=False, default=False)
    points: Mapped[int] = mapped_column(nullable=True, default=0)
    finished_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                  server_default=func.current_timestamp(),
                                                  deferred=True, deferred_group="date")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 deferred=True, deferred_group="date")


class CourseStatistics(Base):
    __tablename__ = "course_statistics"
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), primary_key=True, index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), primary_key=True, index=True, nullable=False)
    last_task: Mapped[int] = mapped_column(ForeignKey("course_task.id"), nullable=True)
    last_action_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                     deferred=True, deferred_group="date")
    total_points: Mapped[int] = mapped_column(default=0)
    finished: Mapped[bool] = mapped_column(nullable=False, default=False)
    finished_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                  deferred=True, deferred_group="date")

    course: Mapped["Course"] = relationship("Course", backref="course_statistics")


class CourseFiles(Base):
    __tablename__ = "course_files"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("course_task.id"), nullable=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("course_message.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, default="file", index=True)
    s3_path: Mapped[str] = mapped_column(nullable=False)
    owner: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False, index=True)

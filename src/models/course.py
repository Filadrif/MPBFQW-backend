from datetime import datetime
from typing import List, Any, Dict

from passlib.context import CryptContext
from sqlalchemy import ARRAY, Integer, TIMESTAMP, func, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, apply_task_type
from schemas.enums import EnumTaskType


class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)
    owner: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True, nullable=False)


class CourseInfo(Base):
    __tablename__ = "course_info"
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), primary_key=True, nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    course_tags: Mapped[List[str]] = mapped_column(ARRAY(String, dimensions=1), default=[])
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 server_default=func.current_timestamp(),
                                                 deferred=True, deferred_group="date")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 deferred=True, deferred_group="date")


class CourseMessage(Base):
    __tablename__ = "course_message"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True, nullable=False)
    content: Mapped[Dict[Any, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 server_default=func.current_timestamp(),
                                                 deferred=True, deferred_group="date")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                 deferred=True, deferred_group="date")


class CourseSection(Base):
    __tablename__ = "course_section"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    is_opened: Mapped[bool] = mapped_column(nullable=False, default=True)


class CourseLesson(Base):
    __tablename__ = "course_lesson"


class CourseTask(Base):
    __tablename__ = "course_task"


class CourseProgress(Base):
    __tablename__ = "course_progress"
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), primary_key=True, index=True, nullable=False)
    task_id: Mapped[int]
    finished: Mapped[bool] = mapped_column(nullable=False, default=False)
    points: Mapped[int]
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



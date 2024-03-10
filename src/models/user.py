from datetime import datetime
from typing import List, Any, Dict

from passlib.context import CryptContext
from sqlalchemy import ARRAY, Integer, TIMESTAMP, func, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, apply_account_type, apply_task_type, apply_gender_type
from schemas.enums import EnumAccountType

pwd_context = CryptContext(schemes=["sha256_crypt"])


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True, deferred=True, deferred_group="sensitive")
    email: Mapped[str] = mapped_column(nullable=False, unique=True, deferred=True, deferred_group="sensitive")
    __password: Mapped[str] = mapped_column("password", nullable=False, deferred=True,
                                            deferred_group="sensitive")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)
    account_type: Mapped[EnumAccountType] = mapped_column(apply_account_type, nullable=False, index=True)
    password_changed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True,
                                                          server_default=func.current_timestamp(),
                                                          deferred=True, deferred_group="date")

    sessions: Mapped[List["AccountSession"]] = relationship(back_populates="account", uselist=True,
                                                            passive_deletes=True)

    @hybrid_property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        # TODO: Add password validation
        self.__password = pwd_context.hash(password)

    @hybrid_method
    def verify_password(self, password):
        return pwd_context.verify(password, self.__password)


class AccountSession(Base):
    __tablename__ = "account_session"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete='CASCADE'), nullable=False, index=True)
    fingerprint: Mapped[str] = mapped_column(nullable=False)
    invalid_after: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    identity: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["Account"] = relationship(back_populates="sessions", uselist=False, passive_deletes=True)

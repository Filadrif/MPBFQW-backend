from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

apply_account_type = ENUM('admin', 'teacher', 'student', name="apply_account_type", metadata=Base.metadata)
apply_task_type = ENUM('typing', 'video', 'quiz', name="apply_task_type", metadata=Base.metadata)
apply_gender_type = ENUM('male', 'female', name="apply_gender_type", metadata=Base.metadata)

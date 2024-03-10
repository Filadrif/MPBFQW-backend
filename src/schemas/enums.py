from enum import StrEnum


class EnumAccountType(StrEnum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class EnumTaskType(StrEnum):
    typing = "typing"
    video = "video"
    quiz = "quiz"


class EnumGenderType(StrEnum):
    male = "male"
    female = "female"

from fastapi import HTTPException, status


def with_errors(*errors: HTTPException):
    d = {}
    for err in errors:
        if err.status_code in d:
            d[err.status_code]["description"] += f"\n\n{err.detail}"
        else:
            d[err.status_code] = {"description": err.detail}
    return d


def invalid_credentials():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Invalid credentials")


def token_validation_failed():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Failed token validation")


def unauthorized():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Authorization check failed")


def token_expired():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail="Token expired")


def access_denied():
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                         detail="Access denied")


def user_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="User not found!")


def user_create_error(message="Unable to create such user!"):
    return HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                         detail=message)


def not_implemented():
    return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                         detail="Not yet implemented")


def file_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="File not found!")


def course_name_is_not_unique():
    return HTTPException(status_code=status.HTTP_409_CONFLICT,
                         detail="Course with such name already exists!")


def course_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Course not found")


def course_section_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Course section not found")


def course_registration_already_exists():
    return HTTPException(status_code=status.HTTP_409_CONFLICT,
                         detail="User already registered on this course!")


def database_transaction_error():
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                         detail="Server can't send your data to database!")


def section_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Section not found")


def lesson_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Lesson not found")


def task_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Task not found")

def phone_is_not_unique():
    return HTTPException(status_code=status.HTTP_409_CONFLICT,
                         detail="User with such phone already exists!")


def course_message_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Course message not found")

def attachment_not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="Attachment file not found")
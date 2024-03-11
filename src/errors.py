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

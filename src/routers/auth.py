import sqlalchemy.exc
from fastapi import APIRouter, Depends, Request, Response, Body, Cookie
from sqlalchemy import or_
from datetime import datetime
from sqlalchemy.orm import load_only
import errors
from models.user import Account, AccountInfo
from db import get_database, Session
from schemas.auth import UserCredentials, Refresh, SignUp
from schemas.enums import EnumAccountType
from auth import init_user_tokens, get_user_session, refresh_user_tokens


router = APIRouter()


@router.post("/login", response_model=Refresh,
             responses=errors.with_errors(errors.invalid_credentials(), 
                                          errors.token_validation_failed(),
                                          errors.token_expired()))
async def login_user(
        request: Request,
        response: Response,
        credentials: UserCredentials,
        db: Session = Depends(get_database)
):
    user = db.query(Account).filter(or_(Account.username == credentials.login,
                                        Account.email == credentials.login)).first()
    if user is None:
        raise errors.invalid_credentials()
    if not user.verify_password(credentials.password):
        raise errors.invalid_credentials()
    return init_user_tokens(user, credentials.remember_me, request, response, db)


@router.delete("/logout", status_code=204,
               responses=errors.with_errors(errors.unauthorized(), 
                                            errors.token_expired(),
                                            errors.token_validation_failed()))
async def logout_user(response: Response, user_session=Depends(get_user_session),
                      db: Session = Depends(get_database)):
    response.delete_cookie(key="access")
    db.delete(user_session)
    db.commit()


@router.post("/refresh", response_model=Refresh,
             responses=errors.with_errors(errors.unauthorized(), 
                                          errors.token_expired(),
                                          errors.token_validation_failed(),
                                          errors.phone_is_not_unique()))
async def refresh(
        request: Request,
        response: Response,
        access: str = Cookie(None),
        params: Refresh = Body(),
        db: Session = Depends(get_database)
):
    return refresh_user_tokens(access, params.refresh, request, response, db)


@router.post("/signup", status_code=201)
async def signup_user(credentials: SignUp, db: Session = Depends(get_database)):
    if len(credentials.username) < 3:
        raise errors.user_create_error("Username is too short (must be >3 symbols)!")

    if len(credentials.password) < 8:
        raise errors.user_create_error("Password is too short (must be >8 symbols)!")

    if db.query(Account).filter(or_(Account.username == credentials.username,
                                    Account.email == credentials.email)).first():
        raise errors.user_create_error("User with such username or email already exits!")

    if db.query(AccountInfo).options(load_only(AccountInfo.phone)).filter_by(phone=credentials.phone).first() is not None:
        raise errors.phone_is_not_unique()
    
    new_user = Account(username=credentials.username,
                       email=credentials.email,
                       password=credentials.password,
                       account_type=EnumAccountType.student if credentials.student else EnumAccountType.teacher,
                       is_active=True)
    db.add(new_user)
    db.flush()
    try:
        new_user_info = AccountInfo(account_id=new_user.id,
                                    name=credentials.name,
                                    surname=credentials.surname,
                                    patronymic=credentials.patronymic,
                                    gender=credentials.gender,
                                    phone=credentials.phone,
                                    date_joined=datetime.now(),
                                    date_of_birth=credentials.date_of_birth)
        db.add(new_user_info)
    except sqlalchemy.exc.IntegrityError:
        db.rollback()

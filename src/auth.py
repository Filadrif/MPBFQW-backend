import json
import re
from typing import Dict, Any, Union

from fastapi import Request, Response, Cookie, Depends

import jwt
from datetime import datetime, timedelta, timezone
import uuid

import errors
from models.user import Account, AccountSession
from schemas.auth import Refresh
from schemas.enums import EnumAccountType
from db import Session, get_database
from settings import settings


agent_parse = re.compile(r"^([\w]*)\/([\d\.]*)\s*(\((.*?)\)\s*(.*))?$")


def set_cookie(access: str, response: Response, max_age: int):
    response.set_cookie("access", access, httponly=True, samesite="lax", max_age=max_age)


def get_user_agent_info(request: Request):
    ip = request.client[0]
    user_agent = request.headers.get("user-agent")
    if "X-Forwarded-For" in request.headers:
        info = [request.headers["X-Forwarded-For"]]
    elif "Forwarded" in request.headers:
        info = [request.headers["Forwarded"]]
    else:
        info = [ip]
    match = agent_parse.fullmatch(user_agent)
    if match:
        info += list(match.groups())
    return "".join(json.dumps(info, ensure_ascii=False, separators=(",", ":")))


def encode_token(payload) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_token(token: str, token_type: str, suppress: bool = False) -> Dict[str, Any]:
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'],
                          options={"require": ["exp", "role", "session", "type", "identity"]})
        if data["role"] != token_type:
            raise errors.token_validation_failed()
        return data
    except jwt.ExpiredSignatureError:
        if suppress:
            data = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'],
                              options={"verify_signature": False})
            if data["role"] != token_type:
                raise errors.token_validation_failed()
            return data
        raise errors.token_expired()
    except jwt.DecodeError:
        raise errors.token_validation_failed()


def create_token(long: bool, request: Request, db: Session, account: Union[Account, AccountSession]):
    now = datetime.now(timezone.utc)
    identity = f"{uuid.uuid1(int(now.timestamp()))}"
    if isinstance(account, Account):
        session = AccountSession()
        session.account = account
        session.fingerprint = get_user_agent_info(request)
    else:
        session = account

    session.identity = identity
    if long:
        session.invalid_after = now + timedelta(hours=settings.JWT_REFRESH_LONG_EXPIRE)
        max_age = settings.JWT_REFRESH_LONG_EXPIRE * 3600
    else:
        session.invalid_after = now + timedelta(hours=settings.JWT_REFRESH_EXPIRE)
        max_age = settings.JWT_REFRESH_EXPIRE * 3600
    if isinstance(account, Account):
        db.add(session)
    db.commit()

    access_payload = {
        "role": "access",
        "session": session.id,
        "identity": identity,
        "type": "user",
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE)
    }
    refresh_payload = {
        "role": "refresh",
        "session": session.id,
        "identity": identity,
        "type": f"user:{long}",
        "exp": session.invalid_after
    }
    return access_payload, refresh_payload, max_age


def init_user_tokens(account: Account, long: bool, request: Request, response: Response, db: Session) -> Refresh:
    access_payload, refresh_payload, max_age = create_token(long, request, db, account)
    access = encode_token(access_payload)
    refresh = encode_token(refresh_payload)
    set_cookie(access, response, max_age)
    return Refresh(refresh=refresh)


def check_session(session: str, identity: str, request: Request, db: Session):
    session: AccountSession = db.query(AccountSession).get(session)
    if session is None:
        return None
    if session.fingerprint != get_user_agent_info(request) or session.identity != identity:
        db.delete(session)
        db.commit()
        return None
    return session


def verify_user_access(access: str, request: Request, db: Session) -> AccountSession:
    access_payload = decode_token(access, "access")
    session = check_session(access_payload["session"], access_payload["identity"], request, db)
    if session is None:
        raise errors.unauthorized()
    return session


def refresh_user_tokens(access: str, refresh: str, request: Request, response: Response, db: Session) -> Refresh:
    access_payload = decode_token(access, "access", suppress=True)
    refresh_payload = decode_token(refresh, "refresh")
    if access_payload["identity"] != refresh_payload["identity"]:
        raise errors.token_validation_failed()
    session = check_session(access_payload["session"], access_payload["identity"], request, db)
    if session is None:
        raise errors.unauthorized()

    access_payload, refresh_payload, max_age = create_token(refresh_payload["type"].endswith("True"), request, db)
    access = encode_token(access_payload)
    refresh = encode_token(refresh_payload)
    set_cookie(access, response, max_age)
    return Refresh(refresh=refresh)


async def get_user_session(request: Request, access: str = Cookie(None),
                           db: Session = Depends(get_database)) -> AccountSession:
    return verify_user_access(access, request, db)


async def get_user(session: AccountSession = Depends(get_user_session)) -> Account:
    if session.account.is_active:
        return session.account
    else:
        return errors.access_denied()


async def get_teacher(session: AccountSession = Depends(get_user_session)) -> Account:
    if ((session.account.account_type == EnumAccountType.teacher or
         session.account.account_type == EnumAccountType.admin)
            and session.account.is_active):
        return session.account
    else:
        raise errors.access_denied()


async def get_admin(session: AccountSession = Depends(get_user_session)) -> Account:
    if session.account.account_type == EnumAccountType.admin and session.account.is_active:
        return session.account
    else:
        raise errors.access_denied()

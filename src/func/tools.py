from sqlalchemy.orm import load_only
from models.user import AccountInfo
from db import get_database, Session, with_database
from functools import lru_cache


@lru_cache
def get_user_full_name(account_id: int) -> str:
    """Returns full name of user"""
    with with_database() as db:
        owner_info = (db.query(AccountInfo).
                    options(load_only(AccountInfo.name,
                                    AccountInfo.surname,
                                    AccountInfo.patronymic)).
                    filter_by(account_id=account_id).
                    first())
        if owner_info.patronymic is None:
            owner_name = owner_info.surname + " " + owner_info.name
        else:
            owner_name = owner_info.surname + " " + owner_info.name + " " + owner_info.patronymic
        
        return owner_name

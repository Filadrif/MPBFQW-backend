from sqlalchemy import text
from schemas.enums import EnumAccountType
from settings import settings
from db.session import engine, with_database

import models


def create_initial_user():
    with with_database() as db:
        # Check for existing initial user
        if db.query(models.user.Account).count():
            return

        # Create initial users
        db.add(models.user.Account(
            id=1,
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            is_active=True,
            account_type=EnumAccountType.admin
        ))
        db.add(models.user.AccountInfo(
            account_id=1,
            name="Admin",
            surname="Root",
        ))
        # Set next value for account id sequence
        with engine.connect() as conn:
            conn.execute(text("SELECT setval('account_id_seq',1,true)"))

        db.commit()


def initdb():
    with with_database() as db:
        try:
            db.execute(text("CREATE EXTENSION hstore;"))
        except:
            pass
    models.base.Base.metadata.create_all(engine)
    try:
        create_initial_user()
    except Exception as exsp:
        print(exsp)
        print(type(exsp))

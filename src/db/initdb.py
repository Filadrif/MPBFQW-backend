from sqlalchemy import text

from settings import settings
from db.session import engine, with_database

import models


def create_initial_user():
    with with_database() as db:
        # Check for existing initial user
        if db.query(models.user.Account).count():
            return

        # Create initial users

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

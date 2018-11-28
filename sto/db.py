import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models.implementation import Base


def setup_database(logger, db_filename):

    # https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html
    url = "sqlite+pysqlite:///" + db_filename

    engine = create_engine(url, echo=False)

    if not os.path.exists(db_filename):
        logger.info("Initializing new database %s", db_filename)
        init_db(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def init_db(engine):
    Base.metadata.create_all(engine)


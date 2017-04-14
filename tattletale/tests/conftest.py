import logging
import sys
import pytest
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy_utils.functions as suf
import tattletale.tests.config as tt_config
from tattletale.database.models import Base


@pytest.fixture(scope="session")
def log():
    logging.basicConfig(stream=sys.stdout,
                        format="%(asctime)s %(levelname)-5s %(message)s",
                        level=logging.DEBUG)
    return logging.getLogger()


class TestDatabase(object):
    def __init__(self):
        # Is there an existing database?
        if not suf.database_exists(tt_config.CONNECTION_STRING):
            print("Creating database: %s", tt_config.CONNECTION_STRING)
            suf.create_database(tt_config.CONNECTION_STRING)

        # Create the engine and models. Recreate all tables from scratch.
        self.engine = create_engine(tt_config.CONNECTION_STRING, echo=True)
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        # Create the session
        sessionclass = sessionmaker(bind=self.engine)
        self.session = sessionclass()


@pytest.fixture(scope="session")
def database():
    return TestDatabase()
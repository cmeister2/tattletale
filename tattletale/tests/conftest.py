import logging
import os
import sys
import pytest
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy_utils.functions as suf
from tattletale.database.models import Base
from tattletale.core.configuration import Configuration


@pytest.fixture(scope="session")
def log():
    logging.basicConfig(stream=sys.stdout,
                        format="%(asctime)s %(levelname)-5s %(message)s",
                        level=logging.DEBUG)
    return logging.getLogger()


class TestDatabase(object):
    def __init__(self):
        test_dir = os.path.dirname(__file__)
        test_config = Configuration(os.path.join(test_dir, "test_config.yml"))
        connection_string = CONNECTION_STRING_MAP[test_config["database_type"]]

        # Is there an existing database?
        if not suf.database_exists(connection_string):  # pragma: no cover
            print("Creating database: %s", connection_string)
            suf.create_database(connection_string)

        # Create the engine and models. Recreate all tables from scratch.
        self.engine = create_engine(connection_string, echo=True)
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        # Create the session
        sessionclass = sessionmaker(bind=self.engine)
        self.session = sessionclass()


@pytest.fixture(scope="session")
def database():
    return TestDatabase()


CONNECTION_STRING_MAP = {
    "sqlite_memory": "sqlite://"
}
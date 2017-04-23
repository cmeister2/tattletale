from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from tattletale.database.utility import get_or_create


VersionBase = declarative_base()
CURRENT_VERSION = 1


class VersionInfo(VersionBase):
    """
    Information about the current workspace version
    """
    __tablename__ = "versioninfo"

    id = Column(Integer, primary_key=True)
    version = Column(Integer)


def get_version(engine, session):
    # Ensure that the version table is created.
    VersionBase.metadata.create_all(engine)

    # Query the table for the version row.
    version_row, _created = get_or_create(session, VersionInfo, defaults={"version": CURRENT_VERSION}, id=1)
    return version_row.version
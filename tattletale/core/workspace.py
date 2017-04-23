import logging
import sqlalchemy_utils.functions as sufunc
import sqlalchemy.engine as saengine
import sqlalchemy.orm as saorm
import tattletale.core.configuration as tcconf
import tattletale.database.utility as tdutil
import tattletale.database.version as tdvers
log = logging.getLogger(__file__)


class Workspace(object):
    """
    An object representing an area of investigation.
    """
    def __init__(self,
                 identifier,
                 config_file=None):
        # Load configuration.
        self.config = tcconf.Configuration(config_file=config_file)

        # Work out what connection string to use for this workspace
        self.connection_string = tdutil.connection_string_for_workspace(self.config["database_type"],
                                                                        identifier,
                                                                        self.config)
        log.debug("Using connection string: %s", self.connection_string)

        # Create a database connection.
        if not sufunc.database_exists(self.connection_string):  # pragma: no cover
            log.debug("Database does not exist, creating: %s", self.connection_string)
            sufunc.create_database(self.connection_string)

        self.engine = saengine.create_engine(self.connection_string)

        # Set up a database session.
        session_class = saorm.sessionmaker(bind=self.engine)
        self.session = session_class()

        # Do a version check on the database
        self.version = tdvers.get_version(self.engine, self.session)
import yaml
import os


class Configuration(object):
    CONFIG_FILE_NAME = "config.yml"

    """
    Class representing the configuration.
    """
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.data = None

        # We have to discover the location of the configuration file if one is not specified.
        if self.config_file is None:
            self.config_file = self.discover()

        # Open the config file and load the configuration from it.
        if self.config_file is not None:
            with open(self.config_file, "rb") as f:
                self.data = yaml.safe_load(f)

        # Initialize configuration where necessary
        self.initialize()

    def discover(self):
        # Try and find a config.yml file in the current working directory.
        working_config = os.path.join(os.curdir, self.CONFIG_FILE_NAME)
        if os.path.exists(working_config):
            return working_config

        raise NoConfigFileException("Failed to find a {self.CONFIG_FILE_NAME} file".format(self=self))

    def initialize(self):
        if self.data is None:
            self.data = {}


class NoConfigFileException(Exception):
    pass
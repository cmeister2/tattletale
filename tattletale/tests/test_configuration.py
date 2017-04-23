import tattletale.core.configuration as tc_configuration
import os
import pytest
import tempfile


class TestConfiguration(object):
    def test_discovery(self):
        curdir = os.curdir
        temp_dir = tempfile.mkdtemp()
        print("Made temporary directory for config: {0}".format(temp_dir))
        os.chdir(temp_dir)
        with open(os.path.join(temp_dir, tc_configuration.Configuration.CONFIG_FILE_NAME), "w") as f:
            # Just create the file
            pass

        config = tc_configuration.Configuration()
        os.chdir(curdir)

    def test_no_configuration(self):
        # Switch to a directory where there's no configuration file
        curdir = os.curdir
        os.chdir("/tmp")
        with pytest.raises(tc_configuration.NoConfigFileException):
            config = tc_configuration.Configuration()

        os.chdir(curdir)

    def test_load_config(self):
        test_dir = os.path.dirname(__file__)
        config = tc_configuration.Configuration(os.path.join(test_dir, "test_config.yml"))

        # Check the configuration
        assert(config["database_type"] == "sqlite_memory")

        config["something_random"] = "some value"
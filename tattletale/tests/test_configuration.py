import tattletale.core.configuration as tc_configuration
import os
import pytest


class TestConfiguration(object):
    def test_configuration(self):
        config = tc_configuration.Configuration()

    def test_no_configuration(self):
        # Switch to a directory where there's no configuration file
        curdir = os.curdir
        os.chdir("/tmp")
        with pytest.raises(tc_configuration.NoConfigFileException):
            config = tc_configuration.Configuration()

        os.chdir(curdir)
from tattletale.core.workspace import Workspace


class TestWorkspace(object):
    def test_workspace(self, test_config_path):
        workspace = Workspace("test", config_file=test_config_path)
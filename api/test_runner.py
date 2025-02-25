# test_runner.py

from django.test.runner import DiscoverRunner

class NoTestDBTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, old_config, **kwargs):
        pass

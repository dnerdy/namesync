import filecmp
import os
import shutil
import tempfile

from tests.compat import unittest, mock
from tests.utils import fixture_path, fixture_content

from namesync.main import main
from namesync.packages.six import StringIO
from namesync.records import flatfile_to_records

class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.outfile = StringIO()

        self.scratch_dir = tempfile.mkdtemp()

        def remove_working_dir():
            shutil.rmtree(self.scratch_dir)
        self.addCleanup(remove_working_dir)

        patcher = mock.patch('namesync.backends.dummy.DummyBackend')
        self.DummyBackend = patcher.start()
        self.addCleanup(patcher.stop)

        self.backend = self.DummyBackend.return_value

        with open(fixture_path('example.com')) as f:
            self.backend.records.return_value = flatfile_to_records(f)

    @property
    def config_path(self):
        return os.path.join(self.scratch_dir, '.namesync')

    def use_config(self, name):
        shutil.copy(fixture_path('configs', name), self.config_path)

    def namesync(self, *extra_args):
        argv = ('--config', self.config_path, '--provider', 'dummy') + extra_args
        main(argv, self.outfile)

    def make_mock_input(self, response):
        def input(prompt):
            self.outfile.write(prompt)
            self.outfile.write(response)
            self.outfile.write('\n')
            return response
        return input

class IntegrationTests(IntegrationTestCase):
    def setUp(self):
        super(IntegrationTests, self).setUp()

        self.use_config('namesync-v2.conf')

    def test_nothing_should_happen_when_flatfile_and_api_are_in_sync(self):
        self.namesync(fixture_path('example.com'))
        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), 'All records up to date.\n')
        self.assertEqual(len(self.backend.records.mock_calls), 1)

    def test_updating_zone_should_output_changes_and_call_api(self):
        self.namesync('--zone', 'example.com', '--yes', fixture_path('example.com.updated'))
        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), '''\
ADD    CNAME www  example.com
UPDATE A     test 10.10.10.12
REMOVE A     *    10.10.10.10
''')
        self.assertEqual(len(self.backend.records.mock_calls), 1)
        self.assertEqual(len(self.backend.add.mock_calls), 1)
        self.assertEqual(len(self.backend.update.mock_calls), 1)
        self.assertEqual(len(self.backend.delete.mock_calls), 1)

    @mock.patch('namesync.packages.six.moves.input')
    def test_updating_zone_is_interactive(self, mock_input):
        mock_input.side_effect = self.make_mock_input('y')

        self.namesync('--zone', 'example.com', fixture_path('example.com.updated'))
        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), '''\
The following changes will be made:
ADD    CNAME www  example.com
UPDATE A     test 10.10.10.12
REMOVE A     *    10.10.10.10
Do you want to continue? [y/N] y
ADD    CNAME www  example.com
UPDATE A     test 10.10.10.12
REMOVE A     *    10.10.10.10
''')

        # The same API calls as test_updating_zone_should_output_changes_and_call_api()
        self.assertEqual(len(self.backend.mock_calls), 4)

    @mock.patch('namesync.packages.six.moves.input')
    def test_updating_zone_can_be_aborted(self, mock_input):
        mock_input.side_effect = self.make_mock_input('n')

        with self.assertRaises(SystemExit) as cm:
            self.namesync('--zone', 'example.com', fixture_path('example.com.updated'))

        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), '''\
The following changes will be made:
ADD    CNAME www  example.com
UPDATE A     test 10.10.10.12
REMOVE A     *    10.10.10.10
Do you want to continue? [y/N] n
Abort.
''')

        # There are no API calls other than the initial call to retrieve the records
        self.assertEqual(len(self.backend.mock_calls), 1)
        self.assertEqual(cm.exception.code, 1)

    def test_get_does_not_overwrite_an_existing_file(self):
        path = os.path.join(self.scratch_dir, 'example.com')
        shutil.copy(fixture_path('example.com.updated'), path)

        with self.assertRaises(SystemExit) as cm:
            self.namesync('--get', path)

        self.assertEqual(cm.exception.code, 1)
        self.assertTrue(filecmp.cmp(path, fixture_path('example.com.updated')))

        # Only one API call made to retrieve the records
        self.assertEqual(len(self.backend.mock_calls), 1)

    def test_get_writes_existing_records(self):
        path = os.path.join(self.scratch_dir, 'example.com')

        with self.assertRaises(SystemExit) as cm:
            self.namesync('--get', path)

        self.assertEqual(cm.exception.code, 0)

        self.assertTrue(filecmp.cmp(path, fixture_path('example.com')))

        # Only one API call made to retrieve the records
        self.assertEqual(len(self.backend.mock_calls), 1)

class ConfigMigrationTestCase(IntegrationTestCase):
    def test_config_directory_is_replaced_with_file(self):
        os.mkdir(self.config_path)
        shutil.copy(fixture_path('configs', 'namesync-v2.conf'), os.path.join(self.config_path, 'namesync.conf'))
        self.namesync(fixture_path('example.com'))
        self.assertTrue(os.path.exists(self.config_path))
        self.assertFalse(os.path.isdir(self.config_path))

    def test_v1_config_is_migrated(self):
        self.use_config('namesync-v1.conf')
        self.namesync(fixture_path('example.com'))
        self.assertEqual(fixture_content(self.config_path), fixture_content('configs/namesync-v2.conf'))

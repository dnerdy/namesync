import os
import shutil
import tempfile

from tests.compat import unittest, mock
from tests.utils import fixture_path, fixture_content

from namesync.main import main
from namesync.packages.six import StringIO

class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.outfile = StringIO()

        self.scratch_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.scratch_dir, 'namesync')
        shutil.copytree(fixture_path('namesync'), self.data_dir)
        def remove_working_dir():
            shutil.rmtree(self.scratch_dir)
        self.addCleanup(remove_working_dir)

        patcher = mock.patch('namesync.backends.cloudflare.requests')
        self.requests = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_requests_get_content(fixture_content('example.com.json'))

    def namesync(self, *extra_args):
        argv = ('--data-dir', self.data_dir) + extra_args
        main(argv, self.outfile)

    def mock_requests_get_content(self, content):
        text = mock.PropertyMock(return_value=content)
        response = mock.PropertyMock()
        type(response).text = text
        self.requests.get.return_value = response

    def make_mock_input(self, response):
        def input(prompt):
            self.outfile.write(prompt)
            self.outfile.write(response)
            self.outfile.write('\n')
            return response
        return input

    def test_nothing_should_happen_when_flatfile_and_api_are_in_sync(self):
        self.namesync(fixture_path('example.com'))
        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), 'All records up to date.\n')
        self.assertTrue(self.requests.get.mock_calls == [
            mock.call('https://www.cloudflare.com/api_json.html', params={
                'tkn': u'cafebabe',
                'email': u'user@example.com',
                'a': 'rec_load_all',
                'z': 'example.com',
            }),
        ])

    def test_updating_zone_should_output_changes_and_call_api(self):
        self.namesync('--zone', 'example.com', '--yes', fixture_path('example.com.updated'))
        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), '''\
ADD    CNAME www example.com
UPDATE A     test 10.10.10.12
REMOVE A     * 10.10.10.10
''')
        self.assertTrue(self.requests.get.mock_calls == [
            mock.call('https://www.cloudflare.com/api_json.html', params={
                'tkn': u'cafebabe',
                'email': u'user@example.com',
                'a': 'rec_load_all',
                'z': 'example.com',
            }),
            mock.call('https://www.cloudflare.com/api_json.html', params={
                'tkn': u'cafebabe',
                'email': u'user@example.com',
                'a': 'rec_new',
                'z': 'example.com',
                'type': 'CNAME',
                'name': 'www.example.com',
                'content': 'example.com',
                'ttl': '1',
            }),
            mock.call('https://www.cloudflare.com/api_json.html', params={
                'tkn': u'cafebabe',
                'email': u'user@example.com',
                'a': 'rec_edit',
                'z': 'example.com',
                'id': '00000001',
                'type': 'A',
                'name': 'test.example.com',
                'content': '10.10.10.12',
                'ttl': '1',
                'service_mode': 0,
            }),
            mock.call('https://www.cloudflare.com/api_json.html', params={
                'tkn': u'cafebabe',
                'email': u'user@example.com',
                'a': 'rec_delete',
                'z': 'example.com',
                'id': '00000004',
            }),
        ])

    @mock.patch('namesync.packages.six.moves.input')
    def test_updating_zone_is_interactive(self, mock_input):
        mock_input.side_effect = self.make_mock_input('y')

        self.namesync('--zone', 'example.com', fixture_path('example.com.updated'))
        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), '''\
The following changes will be made:
ADD    CNAME www example.com
UPDATE A     test 10.10.10.12
REMOVE A     * 10.10.10.10
Do you want to continue? [y/N] y
ADD    CNAME www example.com
UPDATE A     test 10.10.10.12
REMOVE A     * 10.10.10.10
''')

        # The same API calls as test_updating_zone_should_output_changes_and_call_api()
        self.assertEqual(len(self.requests.get.mock_calls), 4)

    @mock.patch('namesync.packages.six.moves.input')
    def test_updating_zone_can_be_aborted(self, mock_input):
        mock_input.side_effect = self.make_mock_input('n')

        with self.assertRaises(SystemExit) as cm:
            self.namesync('--zone', 'example.com', fixture_path('example.com.updated'))

        self.outfile.seek(0)
        self.assertEqual(self.outfile.read(), '''\
The following changes will be made:
ADD    CNAME www example.com
UPDATE A     test 10.10.10.12
REMOVE A     * 10.10.10.10
Do you want to continue? [y/N] n
Abort.
''')

        # There are no API calls other than the initial call to retrieve the records
        self.assertEqual(len(self.requests.get.mock_calls), 1)
        self.assertEqual(cm.exception.code, 1)

    def test_cache_directory_should_be_removed_if_it_exists(self):
        cache_dir = os.path.join(self.data_dir, 'cache')
        os.mkdir(cache_dir)
        self.namesync(fixture_path('example.com'))
        self.assertFalse(os.path.exists(cache_dir))

import os
import unittest

from namesync.records import (
    Record,
    flatfile_to_records,
    diff_records,
    records_to_flatfile,
)
from namesync.backends.cloudflare import response_to_records
from namesync.six import StringIO

from tests.utils import fixture_path

def make_record(**kwargs):
    defaults = {
        'type': 'A',
        'name': '.',
        'content': '127.0.0.1',
    }
    defaults.update(kwargs)
    return Record(**defaults)

class RecordTestCase(unittest.TestCase):
    def test_generic_record_defaults(self):
        record = make_record()
        self.assertEqual(record.ttl, 'auto')
        self.assertEqual(record.prio, '0')

    def test_an_a_record_does_not_have_a_prio(self):
        record = make_record(type='A')
        self.assertFalse(record.has_prio)

    def test_an_mx_record_does_have_a_prio(self):
        record = make_record(type='MX')
        self.assertTrue(record.has_prio)

    def test_parse_generic_record(self):
        record = Record.parse('A . 127.0.0.1')
        self.assertTrue(isinstance(record, Record))
        self.assertEqual(record.type, 'A')
        self.assertEqual(record.name, '.')
        self.assertEqual(record.content, '127.0.0.1')

    def test_parse_generic_record_can_parse_quoted_value(self):
        record = Record.parse('TXT name "this is a txt record"')
        self.assertEqual(record.content, 'this is a txt record')

    def test_parse_generic_record_can_parse_ttl(self):
        record = Record.parse('A . 127.0.0.1 300')
        self.assertEqual(record.ttl, '300')

    def test_parse_mx_record(self):
        record = Record.parse('MX . 127.0.0.1')
        self.assertEqual(record.type, 'MX')
        self.assertEqual(record.name, '.')
        self.assertEqual(record.content, '127.0.0.1')

    def test_parse_mx_record_can_parse_prio(self):
        record = Record.parse('MX . 127.0.0.1 2')
        self.assertEqual(record.prio, '2')

    def test_parse_mx_record_can_parse_ttl(self):
        record = Record.parse('MX . 127.0.0.1 2 300')
        self.assertEqual(record.ttl, '300')

    def test_parse_comment(self):
        record = Record.parse('# this is a comment')
        self.assertIsNone(record)

    def test_parse_comment_with_leading_space(self):
        record = Record.parse('  # this is a comment')
        self.assertIsNone(record)

    def test_parse_record_with_comment(self):
        record = Record.parse('A . 127.0.0.1 # this is a comment')
        self.assertIsNotNone(record)

    def test_parse_blank_line(self):
        record = Record.parse('')
        self.assertIsNone(record)

    def test_parse_white_space_only(self):
        record = Record.parse('\t ')
        self.assertIsNone(record)

class RecordEqualityTestCase(unittest.TestCase):
    def test_equality(self):
        reference_record = make_record()
        record = make_record()
        self.assertEqual(record, reference_record)

    def test_equality_on_type(self):
        reference_record = make_record(type='A')
        record = make_record(type='CNAME')
        self.assertNotEqual(record, reference_record)

    def test_equality_on_name(self):
        reference_record = make_record(name='.')
        record = make_record(name='subdomain')
        self.assertNotEqual(record, reference_record)

    def test_equality_on_content(self):
        reference_record = make_record(content='127.0.0.1')
        record = make_record(content='192.168.1.1')
        self.assertNotEqual(record, reference_record)

    def test_equality_on_ttl(self):
        reference_record = make_record(ttl='auto')
        record = make_record(ttl='300')
        self.assertNotEqual(record, reference_record)

    def test_equality_on_prio(self):
        reference_record = make_record(prio='0')
        record = make_record(prio='1')
        self.assertNotEqual(record, reference_record)

class FormatTestCase(unittest.TestCase):
    def test(self):
        zone = 'example.com'

        with open(fixture_path('example.com.json')) as f:
            response_records = response_to_records(zone, f)

        with open(fixture_path('example.com')) as f:
            flatfile = f.read()
            f.seek(0)
            flatfile_records = flatfile_to_records(zone, f)

        self.assertEqual(len(response_records), 5)
        self.assertEqual(len(flatfile_records), 5)
        self.assertEqual(response_records, flatfile_records)

        new_flatfile_file = StringIO()
        records_to_flatfile(flatfile_records, new_flatfile_file)
        new_flatfile_file.seek(0)
        new_flatfile = new_flatfile_file.read()
        self.assertEqual(new_flatfile, flatfile)

class DiffTestCase(unittest.TestCase):
    def test(self):
        one         = make_record(type='A', name='one', content='127.0.0.1')
        one_equal   = make_record(type='A', name='one', content='127.0.0.1')
        two         = make_record(type='MX', name='two', content='127.0.0.1')
        two_update  = make_record(type='MX', name='two', content='127.0.0.2')
        three       = make_record(type='CNAME', name='three', content='127.0.0.1')
        four        = make_record(type='A', name='four', content='127.0.0.1')

        differences = diff_records([one, two, three], [one_equal, four, two_update])

        self.assertEqual(differences['add'], [four])
        self.assertEqual(differences['update'], [two_update])
        self.assertEqual(differences['remove'], [three])

    def test_can_detect_differences_in_records_with_the_same_type_and_name(self):
        one         = make_record(type='MX', name='.', content='127.0.0.1', prio='10')
        one_equal   = make_record(type='MX', name='.', content='127.0.0.1', prio='10')
        two         = make_record(type='MX', name='.', content='127.0.0.2', prio='10')
        two_update  = make_record(type='MX', name='.', content='127.0.0.2', prio='20')
        three       = make_record(type='MX', name='.', content='127.0.0.3', prio='30')
        four        = make_record(type='MX', name='.', content='127.0.0.4', prio='40')

        differences = diff_records([one, two, three], [one_equal, two_update, four])

        self.assertEqual(differences['add'], [four])
        self.assertEqual(differences['update'], [two_update])
        self.assertEqual(differences['remove'], [three])

if __name__ == '__main__':
    unittest.main()

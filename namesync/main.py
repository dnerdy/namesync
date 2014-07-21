#!/usr/bin/env python

import argparse
import functools
import os
import json
import subprocess
import sys

from namesync.backends.cloudflare import CloudFlareBackend
from namesync.config import environment_check
from namesync.records import diff_records, flatfile_to_records

DEFAULT_DATA_LOCATION = os.path.expanduser('~/.namesync')

def main(argv=None, outfile=sys.stdout):
    parser = argparse.ArgumentParser(prog='namesync')
    parser.add_argument('-d', '--data-dir', default=DEFAULT_DATA_LOCATION)
    parser.add_argument('-z', '--zone')
    parser.add_argument('-t', '--dry-run', default=False, action='store_true')
    parser.add_argument('records')

    args = parser.parse_args(argv or sys.argv[1:])

    config = environment_check(args.data_dir)

    zone = args.zone if args.zone else os.path.basename(args.records)
    backend = CloudFlareBackend({'token': config['token'], 'email': config['email']}, zone)
    
    current_records = backend.records()

    with open(args.records) as f:
        new_records = flatfile_to_records(zone, f)

    diff = diff_records(current_records, new_records)

    for record in diff['add']:
        outfile.write('ADD    {}'.format(record))
        outfile.write('\n')
        if not args.dry_run:
            backend.add(record)

    for record in diff['update']:
        outfile.write('UPDATE {}'.format(record))
        outfile.write('\n')
        if not args.dry_run:
            backend.update(record)

    for record in diff['remove']:
        outfile.write('REMOVE {}'.format(record))
        outfile.write('\n')
        if not args.dry_run:
            backend.delete(record)

if __name__ == '__main__':
    main()

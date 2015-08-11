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
from namesync.packages import six

DEFAULT_DATA_LOCATION = os.path.expanduser('~/.namesync')

def action_description(label, record):
    return '{:7}{}'.format(label, record)

class Action(object):
    def __init__(self, description, closure):
        self.description = description
        self.closure = closure

    def apply(self):
        self.closure()

def prompt_user_to_commit():
    response = six.moves.input('Do you want to continue? [y/N] ')
    return response.strip().lower() in ['y', 'yes']

def main(argv=None, outfile=sys.stdout):
    parser = argparse.ArgumentParser(prog='namesync')
    parser.add_argument('-d', '--data-dir', default=DEFAULT_DATA_LOCATION)
    parser.add_argument('-z', '--zone')
    parser.add_argument('-t', '--dry-run', default=False, action='store_true')
    parser.add_argument('-y', '--yes', default=False, action='store_true')
    parser.add_argument('records')

    args = parser.parse_args(argv or sys.argv[1:])

    config = environment_check(args.data_dir)

    zone = args.zone if args.zone else os.path.basename(args.records)
    backend = CloudFlareBackend({'token': config['token'], 'email': config['email']}, zone)
    auto_commit = args.yes

    current_records = backend.records()

    with open(args.records) as f:
        new_records = flatfile_to_records(f)

    diff = diff_records(current_records, new_records)
    actions = []

    for record in diff['add']:
        actions.append(Action(
            description=action_description('ADD', record),
            closure=functools.partial(backend.add, record),
        ))

    for record in diff['update']:
        actions.append(Action(
            description=action_description('UPDATE', record),
            closure=functools.partial(backend.update, record),
        ))

    for record in diff['remove']:
        actions.append(Action(
            description=action_description('REMOVE', record),
            closure=functools.partial(backend.delete, record),
        ))

    def println(message):
        outfile.write(message)
        outfile.write('\n')

    if not len(actions):
        println('All records up to date.')
    else:
        if not auto_commit:
            println('The following changes will be made:')

            for action in actions:
                println(action.description)

        if args.dry_run:
            sys.exit(0)

        commit = auto_commit or prompt_user_to_commit()

        if commit:
            for action in actions:
                println(action.description)
                action.apply()
        else:
            println('Abort.')
            sys.exit(1)


if __name__ == '__main__':
    main()  # pragma: no cover

#!/usr/bin/env python

import argparse
import functools
import os
import json
import subprocess
import sys


from namesync.providers import get_provider
from namesync.config import environment_check
from namesync.records import diff_records, flatfile_to_records, records_to_flatfile
from namesync.packages import six

DEFAULT_CONFIG_LOCATION = os.path.expanduser('~/.namesync')

def action_description(label, record, max_name_length):
    return '{:6} {}'.format(label, record.format(max_name_length))

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
    parser.add_argument('-g', '--get', default=False, action='store_true',
                        help='save existing DNS records to RECORDS')
    parser.add_argument('-z', '--zone',
                        help='specify the zone instead of using the RECORDS filename')
    parser.add_argument('-y', '--yes', default=False, action='store_true',
                        help='sync records without prompting before making changes')
    parser.add_argument('-p', '--provider', default='cloudflare',
                        help='use the specified provider [default: cloudflare]')
    parser.add_argument('-c', '--config', default=DEFAULT_CONFIG_LOCATION,
                        help=(
                            'specify config location [default: ~/.namesync]'
                        ))
    parser.add_argument('records', metavar='RECORDS',
                        help=(
                            'file containing DNS records, one per line. '
                            'The zone is derived from the basename of this file. '
                            'For example, if "dns/example.com" is used then the zone is '
                            'assumed to be "example.com" unless the --zone option is used'
                        ))

    args = parser.parse_args(argv or sys.argv[1:])

    provider_class = get_provider(args.provider)

    config = environment_check(args.config, args.provider, provider_class)

    zone = args.zone if args.zone else os.path.basename(args.records)
    auto_commit = args.yes

    provider_config = config['providers'].get(args.provider, {})
    provider = provider_class(provider_config, zone)

    current_records = provider.records()

    def println(message):
        outfile.write(message)
        outfile.write('\n')

    if args.get:
        if os.path.exists(args.records):
            println('The file "{}" already exists. Refusing to overwrite!'.format(args.records))
            sys.exit(1)

        with open(args.records, 'w') as f:
            records_to_flatfile(current_records, f)

        sys.exit(0)

    with open(args.records) as f:
        new_records = flatfile_to_records(f)

    diff = diff_records(current_records, new_records)
    actions = []

    records = diff['add'] + diff['update'] + diff['remove']

    try:
        max_name_length = max(len(record.name) for record in records)
    except ValueError:
        max_name_length = 0

    for record in diff['add']:
        actions.append(Action(
            description=action_description('ADD', record, max_name_length),
            closure=functools.partial(provider.add, record),
        ))

    for record in diff['update']:
        actions.append(Action(
            description=action_description('UPDATE', record, max_name_length),
            closure=functools.partial(provider.update, record),
        ))

    for record in diff['remove']:
        actions.append(Action(
            description=action_description('REMOVE', record, max_name_length),
            closure=functools.partial(provider.delete, record),
        ))

    if not len(actions):
        println('All records up to date.')
    else:
        if not auto_commit:
            println('The following changes will be made:')

            for action in actions:
                println(action.description)

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

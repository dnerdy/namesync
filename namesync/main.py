#!/usr/bin/env python

from __future__ import print_function

import argparse
import functools
import os
import json
import subprocess

from namesync.records import (
    response_to_records,
    records_to_flatfile,
    flatfile_to_records,
    diff_records,
    make_api_request as unbound_make_api_request,
    get_cached_records,
    full_name,
    get_records_from_api,
)

from namesync.config import (
    zone_cache_path,
    environment_check,
)

DEFAULT_DATA_LOCATION = os.path.expanduser('~/.namesync')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data-dir', default=DEFAULT_DATA_LOCATION)
    parser.add_argument('-r', '--remove-cache', default=False, action='store_true')
    parser.add_argument('-z', '--zone')
    parser.add_argument('-t', '--dry-run', default=False, action='store_true')
    parser.add_argument('records')

    args = parser.parse_args()

    config = environment_check(args.data_dir)
    make_api_request = functools.partial(unbound_make_api_request, email=config['email'], token=config['token'])

    zone = args.zone if args.zone else os.path.basename(args.records)
    zone_cache = zone_cache_path(args.data_dir, zone)
    
    if args.remove_cache:
        if os.path.exists(zone_cache):
            os.unlink(zone_cache)

    cached_records = get_cached_records(zone, zone_cache, make_api_request)

    if not os.path.exists(zone_cache):
        with open(zone_cache, 'wb') as f:
            records_to_flatfile(cached_records, f, cache_format=True)

    with open(args.records) as f:
        records = flatfile_to_records(zone, f)

    diff = diff_records(cached_records, records)

    def record_params(action, record, **extra):
        params={
            'a': action,
            'z': zone,
            'type': record.type,
            'name': full_name(zone, record.name),
            'content': record.content,
            'ttl': record.api_ttl,
        }

        if record.has_prio:
            params['prio'] = record.prio

        params.update(extra)

        return params

    for record in diff['add']:
        print('ADD    {}'.format(record.format(cache_format=False)))
        if not args.dry_run:
            make_api_request(**record_params('rec_new', record))

    for record in diff['update']:
        print('UPDATE {}'.format(record.format(cache_format=False)))
        if not args.dry_run:
            make_api_request(**record_params('rec_edit', record, id=record.id, service_mode=0))

    for record in diff['remove']:
        print('REMOVE {}'.format(record.format(cache_format=False)))
        if not args.dry_run:
            make_api_request(a='rec_delete', z=zone, id=record.id)

    if not args.dry_run and any([diff['add'], diff['update'], diff['remove']]):
        updated_records = get_records_from_api(zone, make_api_request)

        with open(zone_cache, 'wb') as f:
            records_to_flatfile(updated_records, f, cache_format=True)

if __name__ == '__main__':
    main()

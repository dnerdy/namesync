from cStringIO import StringIO
import json

import requests

from namesync.backends.base import Backend
from namesync.exceptions import ApiError
from namesync.records import Record, full_name, short_name


class CloudFlareBackend(Backend):
    def __init__(self, config, zone):
        super(CloudFlareBackend, self).__init__(config, zone)
        self.token = config['token']
        self.email = config['email']

    def records(self):
        r = self.make_api_request(a='rec_load_all')
        response = StringIO(r.text)
        return response_to_records(self.zone, response)

    def add(self, record):
        self.make_api_request(**self.record_params('rec_new', record))

    def update(self, record):
        self.make_api_request(**self.record_params('rec_edit', record, id=record.id, service_mode=0))

    def delete(self, record):
        self.make_api_request(a='rec_delete', id=record.id)

    ## API

    def make_api_request(self, **kwargs):
        params = {
            'email': self.email,
            'tkn': self.token,
            'z': self.zone,
        }
        params.update(kwargs)
        response = requests.get('https://www.cloudflare.com/api_json.html', params=params)
        check_api_response(response)
        return response
    
    def record_params(self, action, record, **extra):
        params={
            'a': action,
            'type': record.type,
            'name': full_name(self.zone, record.name),
            'content': record.content,
            'ttl': record.api_ttl,
        }

        if record.has_prio:
            params['prio'] = record.prio

        params.update(extra)

        return params


def check_api_response(response):
    data = json.loads(response.text)
    if data['result'] == 'error':
        raise ApiError(response.text)

def response_to_records(zone, file):
    data = json.load(file)
    records = []

    if data['response']['recs']['has_more']:
        raise RuntimeException('Not sure what to do with "has_more" in API response')

    for obj in data['response']['recs']['objs']:
        record = Record(
            type=obj['type'],
            name=short_name(zone, obj['name']),
            content=obj['content'],
            id=obj['rec_id'],
        )

        if not obj['auto_ttl']:
            record.ttl = obj['ttl']

        if obj['prio']:
            record.prio = obj['prio']

        records.append(record)

    records.sort()
    return records


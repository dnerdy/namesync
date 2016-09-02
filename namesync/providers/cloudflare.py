import json

from namesync.providers.base import Provider
from namesync.exceptions import ApiError
from namesync.records import Record, full_name, short_name
from namesync.packages import requests
from namesync.packages.six import StringIO


################################################################################

class UnknownZone(ApiError): pass

################################################################################

def cloudflare_url(*components):
    return '/'.join(('https://api.cloudflare.com/client/v4',) + components)

__provider__ = 'CloudFlareProvider'

class CloudFlareResponse(object):
    def __init__(self, data):
        self.data = data

    @property
    def result(self):
        return self.data['result']

    @property
    def result_info(self):
        return self.data['result_info']

    @property
    def count(self):
        return self.result_info['count']

    @property
    def page(self):
        return self.result_info['page']

    @property
    def total_pages(self):
        return self.result_info['total_pages']

    @property
    def has_more(self):
        return self.page < self.total_pages


    # Zones ####################################################################

    @property
    def zone_id(self):
        return self.result[0]['id']

    # DNS Records ##############################################################

    @property
    def records(self):
        return self.result

def wrap_response(response):
    response.raise_for_status()

    # print response.json()
    # print
    # print '*' * 80
    # print

    return CloudFlareResponse(response.json())

class CloudFlareProvider(Provider):
    def __init__(self, config, zone):
        super(CloudFlareProvider, self).__init__(config, zone)
        self.token = config['token']
        self.email = config['email']
        self._zone_id = None

    ############################################################################

    def records(self):
        return [self.make_standard_record(record) for record in self.get_records()]

    def add(self, record):
        data = self.make_api_record(record)

        response = wrap_response(self.api_post(self.dns_records_url(), data))

    def update(self, record):
        record_id = record.data['id']
        data = self.make_api_record(record)

        record.data.update(data)

        response = wrap_response(self.api_put(self.dns_record_url(record_id), record.data))

    def delete(self, record):
        record_id = record.data['id']

        # print 'RECORD ID: ' + str(record_id)

        response = wrap_response(self.api_delete(self.dns_record_url(record_id)))

    ############################################################################

    def zones_url(self):
        return cloudflare_url('zones')

    def dns_records_url(self):
        return cloudflare_url('zones', self.zone_id, 'dns_records')

    def dns_record_url(self, record_id):
        return cloudflare_url('zones', self.zone_id, 'dns_records', record_id)

    ############################################################################

    @property
    def api_headers(self):
        return {
            'X-Auth-Email': self.email,
            'X-Auth-Key': self.token,
        }

    def api_get(self, url, **params):
        return requests.get(url, params=params, headers=self.api_headers)

    def api_post(self, url, json):
        return requests.post(url, json=json, headers=self.api_headers)

    def api_put(self, url, json):
        return requests.put(url, json=json, headers=self.api_headers)

    def api_delete(self, url):
        return requests.delete(url, headers=self.api_headers)

    ############################################################################

    @property
    def zone_id(self):
        if not self._zone_id:
            response = wrap_response(self.api_get(self.zones_url(), name=self.zone))

            if response.count != 1:
                raise UnknownZone

            self._zone_id = response.zone_id

        return self._zone_id

    ############################################################################

    def make_standard_record(self, data):
        return Record(
            name=short_name(self.zone, data['name']),
            type=data['type'],
            content=data['content'],

            # TODO: update Record so that we don't have to know the defaults here
            prio=data.get('priority', '0'),
            ttl=data['ttl'] if data['ttl'] != 1 else 'auto',

            data=data,
        )

    def make_api_record(self, record):
        # TODO: update Record so defaults aren't hardcoded here

        data = {
            'name': full_name(self.zone, record.name),
            'type': record.type,
            'content': record.content,
            'ttl': int(record.ttl) if record.ttl != 'auto' else 1,
        }

        if record.has_prio:
            data['priority'] = int(record.prio)

        return data

    def get_records_for_page(self, page=1):
        return wrap_response(self.api_get(self.dns_records_url(), page=page, per_page=100))

    def get_records(self):
        page = 1

        while True:
            response = self.get_records_for_page(page)

            for record in response.records:
                yield record

            if response.has_more:
                page += 1
            else:
                break

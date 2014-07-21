import functools
import shlex


class RecordParseError(Exception): pass

TTL_DEFAULT = 'auto'
PRIO_DEFAULT = '0'

@functools.total_ordering
class Record(object):
    def __init__(self, type, name, content, prio='0', ttl='auto', id=None):
        self.type = type
        self.name = name
        self.content = content
        self.prio = prio
        self.ttl = ttl
        self.id = id

    def format(self, max_name_len=None):
        max_type_len = 5
        max_name_len = max_name_len or len(self.name)

        components = [
            self.type.ljust(max_type_len),
            self.name.ljust(max_name_len),
            self.quoted_content,
        ]

        if self.output_prio:
            components.append(self.prio)

        if self.output_ttl:
            components.append(self.ttl)

        return ' '.join(components)

    def __str__(self):
        return self.format()

    def __eq__(self, other):
        return all([
            self.type == other.type,
            self.name == other.name,
            self.content == other.content,
            self.prio == other.prio,
            self.ttl == other.ttl,
        ])

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return (self.type, self.name) < (other.type, other.name)

    @classmethod
    def parse(cls, string):
        components = shlex.split(string, comments=True)

        if len(components) == 0:
            return None

        if len(components) < 3:
            raise RecordParseError(string)

        record = cls(
            type=components[0],
            name=components[1],
            content=components[2],
        )

        if len(components) > 3:
            if record.type == 'MX':
                record.prio = components[3]
            else:
                record.ttl = components[3]

        if len(components) > 4 and record.type == 'MX':
            record.ttl = components[4]

        elif len(components) > 5:
            raise RecordParseError(string)

        return record

    @property
    def has_prio(self):
        return self.type == 'MX'

    @property
    def api_ttl(self):
        return '1' if self.ttl == 'auto' else self.ttl

    @property
    def output_prio(self):
        return self.has_prio and (self.prio != PRIO_DEFAULT or self.output_ttl)

    @property
    def output_ttl(self):
        return self.ttl != TTL_DEFAULT

    @property
    def quoted_content(self):
        return repr(str(self.content)) if ' ' in self.content else self.content

def rreplace(s, old, new, maxreplace=None):
    if maxreplace is None:
        other = s.rsplit(old)
    else:
        other = s.rsplit(old, maxreplace)

    return new.join(other)

def short_name(zone, name):
    display_name = rreplace(name, zone, '', 1)
    display_name = display_name.rstrip('.')
    return '.' if display_name == '' else display_name

def full_name(zone, name):
    return zone if name == '.' else '{}.{}'.format(name, zone)

def flatfile_to_records(zone, file):
    records = []
    for line in file:
        record = Record.parse(line)
        if record:
            records.append(record)
    records.sort()
    return records

def records_to_flatfile(records, file):
    max_type_len = 5
    max_name_len = max(len(record.name) for record in records) + 4

    for record in records:
        file.write(record.format(max_name_len))
        file.write('\n')

def make_records_map(records):
    record_map = {}
    for record in records:
        key = (record.type, record.name)
        record_map.setdefault(key, {})[record.content] = record
    return record_map

def diff_records(old, new):
    add = []
    update = []
    remove = []

    old_map = make_records_map(old)
    new_map = make_records_map(new)

    for key, new_content_map in new_map.iteritems():
        if key not in old_map:
            add.extend(new_content_map.values())
        else:
            old_content_map = old_map[key]
            if len(new_content_map) == len(old_content_map) == 1:
                new_record = new_content_map.values()[0]
                old_record = old_content_map.values()[0]
                if new_record != old_record:
                    new_record.id = old_record.id
                    update.append(new_record)
            else:
                for content, new_record in new_content_map.iteritems():
                    if content in old_content_map:
                        old_record = old_content_map[content]
                        if new_record != old_record:
                            new_record.id = old_record.id
                            update.append(new_record)
                    else:
                        add.append(new_record)

    for key, old_content_map in old_map.iteritems():
        if key not in new_map:
            remove.extend(old_content_map.values())
        else:
            new_content_map = new_map[key]
            if not (len(new_content_map) == len(old_content_map) == 1):
                for content, old_record in old_content_map.iteritems():
                    if content not in new_content_map:
                        remove.append(old_record)

    add.sort()
    update.sort()
    remove.sort()

    return {
        'add': add,
        'update': update,
        'remove': remove,
    }

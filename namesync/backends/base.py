
class Backend(object):
    def __init__(self, config, zone):
        self.zone = zone

    def records(self):
        raise NotImplementedError()

    def add(self, record):
        raise NotImplementedError()

    def update(self, record):
        raise NotImplementedError()

    def delete(self, record):
        raise NotImplementedError()


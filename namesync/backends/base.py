
class Backend(object):
    def __init__(self, config, zone):
        self.zone = zone

    def records(self):
        raise NotImplementedError()  # pragma: no cover

    def add(self, record):
        raise NotImplementedError()  # pragma: no cover

    def update(self, record):
        raise NotImplementedError()  # pragma: no cover

    def delete(self, record):
        raise NotImplementedError()  # pragma: no cover


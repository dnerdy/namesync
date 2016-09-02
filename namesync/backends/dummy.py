from namesync.backends.base import Backend


__provider__ = 'DummyBackend'

class DummyBackend(Backend):
    def records(self):
        return []

    def add(self, record):
        pass

    def update(self, record):
        pass

    def delete(self, record):
        pass

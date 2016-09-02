from namesync.providers.base import Provider


__provider__ = 'DummyProvider'

class DummyProvider(Provider):
    def records(self):
        return []

    def add(self, record):
        pass

    def update(self, record):
        pass

    def delete(self, record):
        pass

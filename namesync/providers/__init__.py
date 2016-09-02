import importlib


def get_provider(provider):
    module = importlib.import_module('namesync.providers.' + provider)

    return getattr(module, module.__provider__)

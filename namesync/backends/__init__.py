import importlib
import inspect

from namesync.backends.base import Backend
from namesync.packages.six import iteritems

def get_backend(backend):
    module = importlib.import_module('namesync.backends.' + backend)

    return getattr(module, module.__provider__)

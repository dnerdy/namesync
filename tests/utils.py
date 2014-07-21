import os

def fixture_path(*path_components):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures', *path_components))

def fixture_content(*path_components):
    with open(fixture_path(*path_components)) as f:
        return f.read()

import json
import os
import shutil
import sys

from namesync.input import get_answer


def config_path(data_path):
    return os.path.join(data_path, 'namesync.conf')

def cache_path(data_path):
    return os.path.join(data_path, 'cache')

def write_config(config, file):
    json.dump(config, file, indent=4)
    file.write('\n')

def update_config(config, file):
    file.seek(0)
    write_config(config, file)

def environment_check(data_path, provider_name, provider_class):
    if os.path.exists(config_path(data_path)):
        # Use data_path as the location for the config file; a directory
        # containing a config file is no longer needed
        temp_path = data_path + '.tmp'
        shutil.move(config_path(data_path), temp_path)
        shutil.rmtree(data_path)
        shutil.move(temp_path, data_path)

    os.umask(0o027)
    if not os.path.exists(data_path):
        interactive_config(data_path)
    os.umask(0o022)

    with open(data_path, 'r+') as f:
        config = json.load(f)

        # v1 -> v2 config migration
        if 'providers' not in config:
            config = {'providers': {'cloudflare': config}}
            update_config(config, f)

        if provider_class.needs_config():
            if provider_name not in config['providers']:
                provider_config = interactive_provider_config(provider_name, provider_class)
                config['providers'][provider_name] = provider_config
                update_config(config, f)
            else:
                provider_config = provider_class.migrate_config(config['providers'][provider_name])
                config['providers'][provider_name] = provider_config

    return config

def interactive_config(data_path):
    create_prompt = '{} does not exist.\n\nWould you like to create a conf file now? [Yn] '.format(data_path)
    create = get_answer(create_prompt, default='y', allowed='yn', lowercase=True)

    if create != 'y':
        sys.exit(1)

    with open(data_path, 'wb') as f:
        write_config({'providers': {}}, f)

def interactive_provider_config(provider_name, provider_class):
    sys.stdout.write('''\

========================================
 provider: {}
========================================

'''.format(provider_name))

    provider_config = provider_class.config()
    sys.stdout.write('\n')

    return provider_config

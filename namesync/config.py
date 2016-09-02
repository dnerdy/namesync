import json
import os
import shutil
import sys

def config_path(data_path):
    return os.path.join(data_path, 'namesync.conf')

def cache_path(data_path):
    return os.path.join(data_path, 'cache')

def write_config(config, file):
    json.dump(config, file, indent=4)
    file.write('\n')

def environment_check(data_path):
    os.umask(0o027)
    if not os.path.exists(config_path(data_path)):
        interactive_config(data_path)
    os.umask(0o022)

    if os.path.exists(cache_path(data_path)):
        shutil.rmtree(cache_path(data_path))

    with open(config_path(data_path), 'r+') as f:
        config = json.load(f)

        # v1 -> v2 config migration
        if 'providers' not in config:
            config = {'providers': {'cloudflare': config}}
            f.seek(0)
            write_config(config, f)

    return config

def get_answer(prompt, allowed=None, lowercase=False, default=None):
    answer = None
    while not answer or (allowed and answer not in allowed):
        answer = raw_input(prompt)
        answer = answer.strip()
        if lowercase:
            answer = answer.lower()
        if default:
            answer = answer or default
    return answer

def interactive_config(data_path):
    create_prompt = '{} does not exist.\n\nWould you like to create a conf file now? [Yn] '.format(config_path(data_path))
    create = get_answer(create_prompt, default='y', allowed='yn', lowercase=True)

    if create != 'y':
        sys.exit(1)

    email = get_answer('CloudFlare email: ')
    token = get_answer('CloudFlare token: ')

    if not os.path.exists(data_path):
        os.mkdir(data_path)

    with open(config_path(data_path), 'wb') as f:
        write_config({'providers': {'cloudflare': {'email': email, 'token': token}}}, f)

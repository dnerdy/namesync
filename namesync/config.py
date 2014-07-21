import json
import os
import shutil
import sys

def config_path(data_path):
    return os.path.join(data_path, 'namesync.conf')

def cache_path(data_path):
    return os.path.join(data_path, 'cache')

def environment_check(data_path):
    os.umask(0027)
    if not os.path.exists(config_path(data_path)):
        interactive_config(data_path)
    os.umask(0022)

    if os.path.exists(cache_path(data_path)):
        shutil.rmtree(cache_path(data_path))

    with open(config_path(data_path)) as f:
        return json.load(f)

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
        json.dump({'email': email, 'token': token}, f)

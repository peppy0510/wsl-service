# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import json


def load_commented_json(path):
    with open(path, 'rb') as file:
        lines = file.read().decode('utf-8').split('\n')
        data = '\n'.join([v for v in lines if not v.strip().startswith('//')])
        data = json.loads(data)
    return data

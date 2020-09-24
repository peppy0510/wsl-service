# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import collections.abc
import json

from collections import namedtuple


def merge_dict(*args, add_keys=True):
    assert len(args) >= 2, 'merge_dict requires at least two dicts to merge'
    rtn_dct = args[0].copy()
    merge_dicts = args[1:]
    for merge_dct in merge_dicts:
        if add_keys is False:
            merge_dct = {key: merge_dct[key] for key in set(rtn_dct).intersection(set(merge_dct))}
        for k, v in merge_dct.items():
            if not rtn_dct.get(k):
                rtn_dct[k] = v
            elif k in rtn_dct and type(v) != type(rtn_dct[k]):  # noqa
                raise TypeError(f'Overlapping keys exist with different types: original is {type(rtn_dct[k])}, new value is {type(v)}')
            elif isinstance(rtn_dct[k], dict) and isinstance(merge_dct[k], collections.abc.Mapping):
                rtn_dct[k] = merge_dict(rtn_dct[k], merge_dct[k], add_keys=add_keys)
            elif isinstance(v, list):
                for list_value in v:
                    if list_value not in rtn_dct[k]:
                        rtn_dct[k].append(list_value)
            else:
                rtn_dct[k] = v
    return rtn_dct


def load_commented_json(path):
    with open(path, 'rb') as file:
        lines = file.read().decode('utf-8').split('\n')
        data = '\n'.join([v for v in lines if not v.strip().startswith('//')])
        data = json.loads(data)
    return data


def json_to_object(data):

    def json_object_hook(d):

        # for k in d.keys():
        #     if k == 'path':
        #         d[k] = str(Path(PROJECT_DIR).joinpath(d[k]).resolve())

        return namedtuple('SETTINGS', d.keys())(*d.values())

    return json.loads(data, object_hook=json_object_hook)

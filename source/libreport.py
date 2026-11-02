# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import json


def format_value(value):
    if isinstance(value, list):
        return ','.join([str(v) for v in value]) or 'none'
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if isinstance(v, dict):
                parts += [f'{k}.{name}={item}' for name, item in v.items()]
            else:
                parts.append(f'{k} {v}')
        return ', '.join(parts) or 'none'
    if value is None or value == '':
        return 'none'
    return str(value)


def report(items, problems, as_json=False):
    '''items are (key, title, value): the key names the value in json, the title in text.'''
    if as_json:
        data = {key: value for key, title, value in items}
        data['problems'] = problems
        print(json.dumps(data, indent=2))
        return 1 if problems else 0

    for key, title, value in items:
        print(f' * {title}')
        print(f'   {format_value(value)}')
        print()

    if not problems:
        print(' * Nothing to fix')
        print()
        return 0

    print(' * Problems')
    for problem in problems:
        print(f'   {problem}')
    print()
    return 1

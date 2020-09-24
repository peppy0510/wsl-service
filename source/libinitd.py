# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


from libbase import execute
from settings import BASH_EXECUTABLE


class initd:

    @classmethod
    def service(self, services):
        if not services:
            return ''
        prefix = 'sudo nohup service'
        # suffix = '>/dev/null 2>&1'
        suffix = 'restart </dev/null >/dev/null 2>&1'
        _scripts = [f'{prefix} {v} {suffix}' for v in services]
        script = ' && '.join(_scripts)
        resp = execute([BASH_EXECUTABLE, '-c', script])
        if _scripts:
            print(' * SERVICES Started')
            print('   {}'.format(', '.join(services)))
        return resp
        # print(resp)

    @classmethod
    def execute(self, scripts):
        if not scripts:
            return ''
        # prefix = 'sudo'
        # _scripts = [f'{prefix} {v}' for v in scripts]
        _scripts = [f'{v}' for v in scripts]
        script = ' && '.join(_scripts)
        resp = execute([BASH_EXECUTABLE, '-c', script])
        if _scripts:
            print(' * SCRIPTS Executed')
            for v in scripts:
                print(f'   {v}')
        return resp

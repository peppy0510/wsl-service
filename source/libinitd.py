# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


from libbase import bash
from libbase import execute


class initd:

    @classmethod
    def execute(self, scripts):
        if not scripts:
            return ''
        resp = execute(bash(' && '.join(scripts)))
        print(' * SCRIPTS Executed')
        for v in scripts:
            print(f'   {v}')
        return resp

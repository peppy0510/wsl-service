# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import ctypes
import sys

from pathlib import Path


class run_as_admin:

    def __init__(self, callback):
        if self.is_admin():
            callback()
        else:
            file = str(Path(sys.argv[0]).resolve())
            params = ' '.join([f'"{v}"' for v in [file] + sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(
                None, 'runas', sys.executable, params, None, 1)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

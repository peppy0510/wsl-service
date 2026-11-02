# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import ctypes
import sys

from pathlib import Path


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


class run_as_admin:

    def __init__(self, callback):
        if is_admin():
            callback()
        else:
            file = str(Path(sys.argv[0]).resolve())
            params = ' '.join([f'"{v}"' for v in [file] + sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(
                None, 'runas', sys.executable, params, None, 1)

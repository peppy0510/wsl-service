# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os
import shutil
import sys

from libbase import powershell
from pathlib import Path
from settings import PROJECT_PATH
from settings import RESTART_SHORTCUT_NAME


class shortcut:

    @classmethod
    def path(self):
        return Path(os.environ.get('APPDATA', '')).joinpath(
            'Microsoft', 'Windows', 'Start Menu', 'Programs', f'{RESTART_SHORTCUT_NAME}.lnk')

    @classmethod
    def create(self):
        script = str(Path(PROJECT_PATH).joinpath('source', 'wslservice.py'))
        icon = shutil.which('wsl.exe') or 'wsl.exe'
        fields = {
            'TargetPath': sys.executable,
            'Arguments': f'"{script}" --restart',
            'WorkingDirectory': PROJECT_PATH,
            'IconLocation': f'{icon},0',
            'Description': 'Restarts the WSL distribution.',
        }
        assignments = '; '.join([f'$s.{k} = {self.quote(v)}' for k, v in fields.items()])
        powershell((f'$s = (New-Object -ComObject WScript.Shell).CreateShortcut('
                    f'{self.quote(str(self.path()))}); {assignments}; $s.Save()'))

    @classmethod
    def remove(self):
        self.path().unlink(missing_ok=True)

    @classmethod
    def show(self):
        print(' * SHORTCUT Start menu')
        print(f'   {self.path() if self.path().exists() else "no"}')
        print()

    @classmethod
    def quote(self, value):
        return "'{}'".format(value.replace("'", "''"))

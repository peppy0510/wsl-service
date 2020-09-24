# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import ctypes
import sys
import winreg

from pathlib import Path


DELEGATE_EXEC_REG_KEY = 'DelegateExecute'


class run_as_admin:

    def __init__(self, callback):
        if self.is_admin():
            callback()
        else:
            # self.bypass_uac()
            # self.create_reg_key(DELEGATE_EXEC_REG_KEY, '')
            file = str(Path(__file__).resolve())
            ctypes.windll.shell32.ShellExecuteW(
                None, 'runas', sys.executable, file, None, 1)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def bypass_uac(self, command):
        try:
            self.create_reg_key(DELEGATE_EXEC_REG_KEY, '')
            self.create_reg_key(None, command)
        except WindowsError:
            raise

    def create_reg_key(self, key, value):
        reg_path = 'Software\\Classes\\ms-settings\\shell\\open\\command'
        try:
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, key, 0, winreg.REG_SZ, value)
            winreg.CloseKey(registry_key)
        except WindowsError:
            raise

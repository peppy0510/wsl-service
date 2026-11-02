# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import configparser
import os
import subprocess

from pathlib import Path
from settings import CWD
from settings import DISTRIBUTION
from settings import WSL_EXECUTABLE


def shutdown():
    execute(f'{WSL_EXECUTABLE} -d {DISTRIBUTION} --shutdown', shell=True)


def bash(script):
    return [WSL_EXECUTABLE, '-d', DISTRIBUTION, '--exec', 'bash', '-c', script]


def distributions(running=False):
    command = [WSL_EXECUTABLE, '--list', '--quiet'] + (['--running'] if running else [])
    try:
        proc = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    # wsl.exe writes UTF-16 unless WSL_UTF8 is set.
    resp = proc.stdout.replace(b'\x00', b'').decode('utf-8', 'ignore')
    return [v.strip() for v in resp.split('\n') if v.strip()]


def is_wsl_vm_running():
    # Anything that asks the distribution itself would start WSL, so look for its VM first.
    resp = execute('tasklist /FI "IMAGENAME eq vmmemWSL" /FO CSV /NH', shell=True,
                   display_error=False) or ''
    return 'vmmemWSL' in resp


def wslconfig_path():
    return Path(os.environ.get('USERPROFILE', '~')).expanduser().joinpath('.wslconfig')


def read_wslconfig():
    '''Every section and key of .wslconfig, or None when it cannot be parsed.'''
    config = configparser.ConfigParser(strict=False, inline_comment_prefixes=('#', ';',))
    config.optionxform = str
    try:
        config.read(str(wslconfig_path()), encoding='utf-8-sig')
    except configparser.Error:
        return None
    return {section: dict(config.items(section)) for section in config.sections()}


def wslconfig_networking_mode():
    config = read_wslconfig()
    if config is None:
        return 'unreadable'
    return config.get('wsl2', {}).get('networkingMode', 'nat').strip().lower()


def powershell(command, display_error=True):
    return execute([
        'powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
        display_error=display_error)


def execute_code(command, shell=False, timeout=None):
    try:
        proc = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, shell=shell, cwd=CWD, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return 1
    return proc.returncode


def execute(command, shell=False, display_error=True, close_fds=True):
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, shell=shell, cwd=CWD, close_fds=close_fds)

    resp = None
    error = None

    try:
        resp, error = proc.communicate()
    except IndexError:
        pass
    except UnicodeDecodeError:
        pass

    if display_error and error and isinstance(error, str):
        print(error)

    return resp

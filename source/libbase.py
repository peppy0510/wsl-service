# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import subprocess

from settings import CWD
from settings import DISTRIBUTION
from settings import WSL_EXECUTABLE


def shutdown():
    execute(f'{WSL_EXECUTABLE} -d {DISTRIBUTION} --shutdown', shell=True)


def bash(script):
    return [WSL_EXECUTABLE, '-d', DISTRIBUTION, '--exec', 'bash', '-c', script]


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

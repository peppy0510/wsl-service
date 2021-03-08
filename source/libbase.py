# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import asyncio
import subprocess
import time

from settings import CWD
from settings import DISTRIBUTION
from settings import WSL_EXECUTABLE


def decode(string):
    resp = None

    try:
        resp = string.decode('utf-8')
    except UnicodeDecodeError:
        pass

    if resp is None:
        try:
            resp = string.decode('cp949')
        except UnicodeDecodeError:
            pass

    if resp is None:
        resp = string.decode('utf-8', 'ignore')

    return resp


def shutdown():
    execute(f'{WSL_EXECUTABLE} -t {DISTRIBUTION}', shell=True)


def execute(command, shell=False, display_error=True):
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=shell, cwd=CWD)

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


async def aioexecute(command, shell=False, display_error=True):

    proc = await asyncio.create_subprocess_exec(
        *command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, shell=shell, cwd=CWD)

    resp = None
    error = None

    try:
        resp, error = await proc.communicate()
        # resp, error = await asyncio.wait_for(proc.communicate(), timeout=10)
    except IndexError:
        pass
    except UnicodeDecodeError:
        pass

    if display_error and error and isinstance(error, str):
        print(error)

    return resp

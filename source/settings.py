# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import os

from libjson import load_commented_json
from libjson import merge_dict
from pathlib import Path

DISTRIBUTION = 'Ubuntu-20.04'

FIREWALL_RULE_NAME = '+WSL'

WSL_EXECUTABLE = str(Path('C:/Windows/System32/wsl.exe'))
BASH_EXECUTABLE = str(Path('C:/Windows/System32/bash.exe'))

default_path = Path(__file__).resolve().parent.joinpath('settings.json')
user_path = Path(__file__).resolve().parent.parent.joinpath('settings.json')

settings = load_commented_json(str(default_path))

if user_path.exists():
    user_settings = load_commented_json(str(user_path))
    settings = merge_dict(settings, user_settings)

INITD_SERVICES = settings.get('INITD_SERVICES', [])
INITD_EXECUTES = settings.get('INITD_EXECUTES', [])

PROXY_FORWARDING_PORTS = settings.get('PROXY_FORWARDING_PORTS', [])
FIREWALL_ALLOWED_PORTS = settings.get('FIREWALL_ALLOWED_PORTS', [])
FIREWALL_ALLOWED_PORTS = sorted(list(set(FIREWALL_ALLOWED_PORTS + PROXY_FORWARDING_PORTS)))

CWD = os.path.expanduser('~')

DELEGATE_EXEC_REG_KEY = 'DelegateExecute'

ANSI_BACKGROUND_WHITE = '\x1b[7m'
ANSI_RESET = '\x1b[0m'

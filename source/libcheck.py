# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import configparser
import os
import subprocess

from pathlib import Path
from settings import BINDING_ADDRESS
from settings import DISTRIBUTION
from settings import EXTERNAL_ADDRESS
from settings import FIREWALL_ALLOWED_PORTS
from settings import KEEPALIVE
from settings import NETWORK_MODE
from settings import PROXY_FORWARDING_TCP_PORTS
from settings import PROXY_FORWARDING_UDP_PORTS
from settings import RESUME_ACTION
from settings import RESUME_PROBE_PORTS
from settings import SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS
from settings import UNKNOWN_SETTINGS
from settings import WSL_EXECUTABLE
from settings import user_path


NETWORK_MODES = ('portproxy', 'mirrored',)
RESUME_ACTIONS = ('restart', 'heal', 'none',)


class check:

    @classmethod
    def run(self):
        problems = []

        self.show('Settings', str(user_path) if user_path.exists() else 'defaults only')
        for key in UNKNOWN_SETTINGS:
            problems.append(f'{key} is not a setting, remove it')

        distributions = self.get_distributions()
        self.show('DISTRIBUTION', DISTRIBUTION)
        if DISTRIBUTION not in distributions:
            problems.append((f'DISTRIBUTION {DISTRIBUTION} is not installed, '
                             f'installed: {", ".join(distributions) or "none"}'))

        wslconfig_mode = self.get_wslconfig_networking_mode()
        self.show('NETWORK_MODE', f'{NETWORK_MODE} (.wslconfig networkingMode={wslconfig_mode})')
        if NETWORK_MODE not in NETWORK_MODES:
            problems.append(f'NETWORK_MODE must be one of {", ".join(NETWORK_MODES)}')
        elif (NETWORK_MODE == 'mirrored') != (wslconfig_mode == 'mirrored'):
            problems.append((f'NETWORK_MODE {NETWORK_MODE} does not match '
                             f'networkingMode={wslconfig_mode} in .wslconfig'))

        self.show('EXTERNAL_ADDRESS', EXTERNAL_ADDRESS)
        if NETWORK_MODE == 'portproxy':
            self.show('BINDING_ADDRESS', BINDING_ADDRESS)
            if BINDING_ADDRESS.split('.')[:3] == EXTERNAL_ADDRESS.split('.')[:3]:
                problems.append(f'BINDING_ADDRESS {BINDING_ADDRESS} is inside the LAN subnet')
            self.show('TCP forwarded to WSL', self.join(PROXY_FORWARDING_TCP_PORTS))
            self.show('UDP relayed by wsludpservice', self.join(
                PROXY_FORWARDING_UDP_PORTS + SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS))
            self.show('Opened on the Windows firewall', self.join(FIREWALL_ALLOWED_PORTS))
        else:
            self.show('Opened on the Windows and Hyper-V firewalls',
                      self.join(FIREWALL_ALLOWED_PORTS))

        self.show('RESUME_ACTION', RESUME_ACTION)
        if RESUME_ACTION not in RESUME_ACTIONS:
            problems.append(f'RESUME_ACTION must be one of {", ".join(RESUME_ACTIONS)}')
        if RESUME_PROBE_PORTS:
            self.show('RESUME_PROBE_PORTS', self.join(RESUME_PROBE_PORTS))

        self.show('KEEPALIVE', KEEPALIVE)

        if not problems:
            print(' * Nothing to fix')
            print()
            return 0

        print(' * Problems')
        for problem in problems:
            print(f'   {problem}')
        print()
        return 1

    @classmethod
    def get_distributions(self):
        try:
            proc = subprocess.run(
                [WSL_EXECUTABLE, '-l', '-q'], stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return []
        # wsl.exe writes UTF-16 unless WSL_UTF8 is set.
        resp = proc.stdout.replace(b'\x00', b'').decode('utf-8', 'ignore')
        return [v.strip() for v in resp.split('\n') if v.strip()]

    @classmethod
    def get_wslconfig_networking_mode(self):
        path = Path(os.environ.get('USERPROFILE', '~')).expanduser().joinpath('.wslconfig')
        config = configparser.ConfigParser(strict=False, inline_comment_prefixes=('#', ';',))
        try:
            config.read(str(path), encoding='utf-8-sig')
        except configparser.Error:
            return 'unreadable'
        return config.get('wsl2', 'networkingMode', fallback='nat').strip().lower()

    @classmethod
    def join(self, ports):
        return ','.join([str(v) for v in sorted(set(ports))]) or 'none'

    @classmethod
    def show(self, title, value):
        print(f' * {title}')
        print(f'   {value}')
        print()

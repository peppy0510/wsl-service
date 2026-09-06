# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import socket
import time

from datetime import datetime
from libbase import execute
from libbase import execute_code
from libhypervfirewall import hypervfirewall
from libportproxy import portproxy
from pathlib import Path
from settings import DISTRIBUTION
from settings import EXTERNAL_ADDRESS
from settings import FIREWALL_ALLOWED_PORTS
from settings import NETWORK_MODE
from settings import PROXY_FORWARDING_TCP_PORTS
from settings import RESUME_LOG_PATH
from settings import RESUME_PROBE_HOST
from settings import RESUME_PROBE_PORTS
from settings import WSL_EXECUTABLE


DEFAULT_ROUTE_COMMAND = ('ip', '-o', '-4', 'route', 'show', 'default',)

SETTLE_RETRIES = 6
SETTLE_DELAY = 5


class resume:

    @classmethod
    def heal(self):
        state = self.probe()
        self.log(f'probe {state}')

        if all(state.values()):
            return True

        if not state['distribution']:
            return False

        if not state['outbound']:
            self.reset_interface()

        if not state['inbound']:
            self.reset_inbound()

        return self.settle()

    @classmethod
    def settle(self):
        for _ in range(SETTLE_RETRIES):
            time.sleep(SETTLE_DELAY)
            state = self.probe()
            self.log(f'probe {state}')
            if all(state.values()):
                return True
        return False

    @classmethod
    def probe(self):
        distribution = self.probe_distribution()
        return {
            'distribution': distribution,
            'outbound': self.probe_outbound() if distribution else False,
            'inbound': self.probe_inbound() if distribution else False,
        }

    @classmethod
    def probe_distribution(self):
        return execute_code([
            WSL_EXECUTABLE, '-d', DISTRIBUTION, '-u', 'root', '--', 'true'], timeout=30) == 0

    @classmethod
    def probe_outbound(self):
        if not self.default_field('via'):
            return False
        if not RESUME_PROBE_HOST:
            return True
        return execute_code([
            WSL_EXECUTABLE, '-d', DISTRIBUTION, '-u', 'root', '--',
            'getent', 'hosts', RESUME_PROBE_HOST], timeout=15) == 0

    @classmethod
    def probe_inbound(self):
        for port in RESUME_PROBE_PORTS:
            try:
                socket.create_connection((EXTERNAL_ADDRESS, port), timeout=5).close()
            except OSError:
                return False
        return True

    @classmethod
    def default_route(self):
        resp = execute([
            WSL_EXECUTABLE, '-d', DISTRIBUTION, '-u', 'root', '--',
        ] + list(DEFAULT_ROUTE_COMMAND), display_error=False)
        return (resp or '').split('\n')[0].split()

    @classmethod
    def default_field(self, keyword):
        parts = self.default_route()
        index = parts.index(keyword) + 1 if keyword in parts else len(parts)
        return parts[index] if index < len(parts) else ''

    @classmethod
    def reset_interface(self):
        device = self.default_field('dev')

        if not device:
            return

        self.log(f'reset interface {device}')
        prefix = [WSL_EXECUTABLE, '-d', DISTRIBUTION, '-u', 'root', '--', 'ip', 'link', 'set', device]
        execute(prefix + ['down'])
        time.sleep(1)
        execute(prefix + ['up'])

    @classmethod
    def reset_inbound(self):
        self.log('reset inbound')

        if NETWORK_MODE == 'mirrored':
            hypervfirewall.remove()
            hypervfirewall.add(FIREWALL_ALLOWED_PORTS)
        else:
            portproxy.reset()
            portproxy.add(PROXY_FORWARDING_TCP_PORTS)

    @classmethod
    def log(self, message):
        print(f' * {message}')
        path = Path(RESUME_LOG_PATH)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'a', encoding='utf-8') as file:
                file.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} {message}\n')
        except OSError:
            pass

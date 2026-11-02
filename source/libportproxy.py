# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import re

from libbase import bash
from libbase import execute
from settings import EXTERNAL_ADDRESS


class portproxy:

    @classmethod
    def reset(self):
        execute('netsh interface portproxy reset', shell=True)

    @classmethod
    def showall(self):
        ip, ports = self.get_registgered()
        print(' * IP Address')
        print(f'   {ip}')
        print()
        print(' * PORTS Proxy Opened')
        print('   {}'.format(','.join([str(v) for v in ports])))
        print()

    @classmethod
    def get_registgered(self):
        resp = execute('netsh interface portproxy show all', shell=True)
        ports = []
        destinations = []
        for line in resp.split('\n'):
            parts = [v for v in line.split(' ') if v]
            if len(parts) != 4 or len(parts) < 3 or not parts[1].isdigit() or not parts[3].isdigit():
                continue
            ports += [int(parts[3])]
            destinations += [parts[2]]

        ports = sorted(list(set(ports)))
        destinations = list(set(destinations))
        destination = destinations[0] if destinations else ''
        return destination, ports

    @classmethod
    def add(self, ports):
        ports = [ports] if isinstance(ports, int) else ports
        ports = sorted(list(set(ports)))
        registered_ip, registered_ports = self.get_registgered()
        wsl_ipaddress = self.get_wsl_ipaddress()

        if registered_ip == wsl_ipaddress and registered_ports == ports:
            return

        self.reset()
        for port in ports:
            execute((
                f'netsh interface portproxy add v4tov4 '
                f'listenport={port} listenaddress={EXTERNAL_ADDRESS} '
                f'connectport={port} connectaddress={wsl_ipaddress}'), shell=True)

    @classmethod
    def get_wsl_ipaddress(self):
        resp = execute(bash('ip -4 -o addr show eth0'), display_error=False) or ''
        return re.findall(r'inet ([0-9]+(?:\.[0-9]+){3})', resp)[0]

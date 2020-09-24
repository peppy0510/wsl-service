# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import re
import subprocess

from libbase import execute
from settings import BASH_EXECUTABLE
from settings import CWD


class portproxy:

    @classmethod
    def reset(self):
        # self.get_registgered()
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
        ports = sorted(ports)
        ports = [ports] if isinstance(ports, int) else ports
        ports = sorted(list(set(ports)))
        registered_ip, registered_ports = self.get_registgered()
        wsl_ipaddress = self.get_wsl_ipaddress()

        if registered_ip == wsl_ipaddress and registered_ports == ports:
            return

        self.reset()
        for port in sorted([ports] if isinstance(ports, int) else ports):
            execute((
                f'netsh interface portproxy add v4tov4 '
                f'listenport={port} listenaddress=0.0.0.0 '
                f'connectport={port} connectaddress={wsl_ipaddress}'), shell=True)

    @classmethod
    def get_wsl_ipaddress(self):
        return '192.168.100.2'

        command = [BASH_EXECUTABLE, '-c', 'ip addr show eth0 | grep "inet\\b" | awk "{print $2}" | cut -d/ -f1']
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=CWD)
        resp, error = proc.communicate()
        resp = re.findall(r'[0-9]+(?:\.[0-9]+){3}', resp)[0]
        return resp

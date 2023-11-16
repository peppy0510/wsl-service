# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


from libbase import execute
from settings import FIREWALL_RULE_NAME


class advfirewall:

    @classmethod
    def add(self, ports):
        ports = sorted(ports)
        ports = [ports] if isinstance(ports, int) else ports
        ports = sorted(list(set(ports)))
        if ports == self.get_registgered():
            return
        self.remove()
        ports = ','.join([str(v) for v in sorted(ports)])
        common = 'netsh advfirewall firewall add rule action=allow'
        for direction in ('in', 'out',):
            for protocol in ('TCP', 'UDP',):
                execute((f'{common} localport={ports} name="{FIREWALL_RULE_NAME}{protocol}" '
                         f'protocol={protocol} dir={direction}'), shell=True)

    @classmethod
    def get_registgered(self):
        ports = []
        for protocol in ('TCP', 'UDP',):
            resp = execute(('netsh advfirewall firewall show rule '
                            f'name="{FIREWALL_RULE_NAME}{protocol}"'), shell=True)
            lines = [v for v in resp.split('\n') if v.startswith(
                'LocalPort:') or v.startswith('RemotePort:')]
            for line in lines:
                line = line.split(':')[-1].strip()
                ports += [int(v) for v in line.split(',') if v.isdigit()]
        return sorted(list(set(ports)))

    @classmethod
    def remove(self):
        for protocol in ('TCP', 'UDP',):
            execute(('netsh advfirewall firewall delete rule '
                     f'name="{FIREWALL_RULE_NAME}{protocol}"'), shell=True)

    @classmethod
    def showall(self):
        ports = self.get_registgered()
        ports = ','.join([str(v) for v in ports])
        print(' * PORTS Firewall Opened')
        print(f'   {ports}')
        print()

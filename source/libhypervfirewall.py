# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


from libbase import powershell
from settings import FIREWALL_RULE_NAME
from settings import HYPERV_VM_CREATOR_ID


class hypervfirewall:

    @classmethod
    def add(self, ports):
        ports = [ports] if isinstance(ports, int) else ports
        ports = sorted(list(set(ports)))
        if ports == self.get_registgered():
            return
        self.remove()
        ports = ','.join([str(v) for v in ports])
        for protocol in ('TCP', 'UDP',):
            powershell((f'New-NetFirewallHyperVRule -VMCreatorId "{HYPERV_VM_CREATOR_ID}" '
                        f'-Name "{FIREWALL_RULE_NAME}{protocol}" '
                        f'-DisplayName "{FIREWALL_RULE_NAME}{protocol}" '
                        f'-Direction Inbound -Protocol {protocol} '
                        f'-LocalPorts {ports} -Action Allow'))

    @classmethod
    def get_registgered(self):
        ports = []
        for protocol in ('TCP', 'UDP',):
            resp = powershell((f'(Get-NetFirewallHyperVRule -Name "{FIREWALL_RULE_NAME}{protocol}" '
                               '-ErrorAction SilentlyContinue).LocalPorts'), display_error=False)
            for line in (resp or '').split('\n'):
                ports += [int(v) for v in line.strip().split(',') if v.strip().isdigit()]
        return sorted(list(set(ports)))

    @classmethod
    def remove(self):
        for protocol in ('TCP', 'UDP',):
            powershell((f'Remove-NetFirewallHyperVRule -Name "{FIREWALL_RULE_NAME}{protocol}" '
                        '-ErrorAction SilentlyContinue'), display_error=False)

    @classmethod
    def showall(self):
        ports = self.get_registgered()
        ports = ','.join([str(v) for v in ports])
        print(' * PORTS Hyper-V Firewall Opened')
        print(f'   {ports}')
        print()

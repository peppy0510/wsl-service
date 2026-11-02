# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


from libbase import distributions
from libbase import read_wslconfig
from libbase import wslconfig_networking_mode
from libbase import wslconfig_path
from libreport import report
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
from settings import user_path


NETWORK_MODES = ('portproxy', 'mirrored',)
RESUME_ACTIONS = ('restart', 'heal', 'none',)


class check:

    @classmethod
    def run(self, as_json=False):
        items = []
        problems = []

        items.append(('settings', 'Settings', str(user_path) if user_path.exists() else None))
        for key in UNKNOWN_SETTINGS:
            problems.append(f'{key} is not a setting, remove it')

        installed = distributions()
        items.append(('DISTRIBUTION', 'DISTRIBUTION', DISTRIBUTION))
        items.append(('installed', 'Installed distributions', installed))
        if DISTRIBUTION not in installed:
            problems.append(f'DISTRIBUTION {DISTRIBUTION} is not installed')

        wslconfig_mode = wslconfig_networking_mode()
        items.append(('NETWORK_MODE', 'NETWORK_MODE', NETWORK_MODE))
        items.append(('wslconfig', '.wslconfig', read_wslconfig()))
        if wslconfig_mode == 'unreadable':
            problems.append(f'{wslconfig_path()} cannot be parsed')
        if NETWORK_MODE not in NETWORK_MODES:
            problems.append(f'NETWORK_MODE must be one of {", ".join(NETWORK_MODES)}')
        elif (NETWORK_MODE == 'mirrored') != (wslconfig_mode == 'mirrored'):
            problems.append((f'NETWORK_MODE {NETWORK_MODE} does not match '
                             f'networkingMode={wslconfig_mode} in .wslconfig'))

        items.append(('EXTERNAL_ADDRESS', 'EXTERNAL_ADDRESS', EXTERNAL_ADDRESS))
        if NETWORK_MODE == 'portproxy':
            items.append(('BINDING_ADDRESS', 'BINDING_ADDRESS', BINDING_ADDRESS))
            if BINDING_ADDRESS.split('.')[:3] == EXTERNAL_ADDRESS.split('.')[:3]:
                problems.append(f'BINDING_ADDRESS {BINDING_ADDRESS} is inside the LAN subnet')
            items.append(('forwarded_tcp_ports', 'TCP forwarded to WSL',
                          sorted(PROXY_FORWARDING_TCP_PORTS)))
            items.append(('relayed_udp_ports', 'UDP relayed by wsludpservice', sorted(
                PROXY_FORWARDING_UDP_PORTS + SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS)))
            items.append(('firewall_ports', 'Opened on the Windows firewall',
                          FIREWALL_ALLOWED_PORTS))
        else:
            items.append(('firewall_ports', 'Opened on the Windows and Hyper-V firewalls',
                          FIREWALL_ALLOWED_PORTS))

        items.append(('RESUME_ACTION', 'RESUME_ACTION', RESUME_ACTION))
        if RESUME_ACTION not in RESUME_ACTIONS:
            problems.append(f'RESUME_ACTION must be one of {", ".join(RESUME_ACTIONS)}')
        items.append(('RESUME_PROBE_PORTS', 'RESUME_PROBE_PORTS', RESUME_PROBE_PORTS))

        items.append(('KEEPALIVE', 'KEEPALIVE', KEEPALIVE))

        return report(items, problems, as_json)

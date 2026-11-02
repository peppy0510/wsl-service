# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import re

from libadvfirewall import advfirewall
from libbase import bash
from libbase import distributions
from libbase import execute
from libbase import is_wsl_vm_running
from libbase import powershell
from libportproxy import portproxy
from libreport import report
from libshortcut import shortcut
from pathlib import Path
from settings import BOOT_TASK_NAME
from settings import DISTRIBUTION
from settings import FIREWALL_ALLOWED_PORTS
from settings import FIREWALL_RULE_NAME
from settings import KEEPALIVE
from settings import NETWORK_MODE
from settings import PROXY_FORWARDING_TCP_PORTS
from settings import RESUME_LOG_PATH
from settings import RESUME_TASK_NAME
from settings import SERVICE_TASK_NAME


TASK_NAMES = (SERVICE_TASK_NAME, RESUME_TASK_NAME, BOOT_TASK_NAME,)

# Addresses that other machines cannot reach, dnsTunneling answers on 10.255.255.254.
LOCAL_ADDRESS = re.compile(r'^(127\.|\[::1\]|::1|10\.255\.255\.254)')

# One PowerShell start costs seconds, so everything it has to answer goes in one script.
WINDOWS_QUERY = '''
foreach ($n in @({tasks})) {{
    $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
    'task|' + $n + '|' + $(if ($t) {{ $t.State }} else {{ 'Missing' }})
}}
foreach ($p in @('TCP', 'UDP')) {{
    $r = Get-NetFirewallHyperVRule -Name ('{rule}' + $p) -ErrorAction SilentlyContinue
    'hyperv|' + $p + '|' + ($r.LocalPorts -join ',')
}}
Get-CimInstance Win32_Process -Filter "Name = 'wsl.exe'" |
    Where-Object {{ $_.CommandLine -like '*sleep infinity*' }} |
    ForEach-Object {{ 'keepalive|' + $_.ProcessId }}
'''


class status:

    @classmethod
    def run(self, as_json=False):
        items = []
        problems = []

        windows = self.query_windows()
        vm_running = is_wsl_vm_running()
        running = vm_running and DISTRIBUTION in distributions(running=True)
        items.append(('DISTRIBUTION', 'DISTRIBUTION', DISTRIBUTION))
        items.append(('running', 'Running', running))

        tasks = windows['tasks']
        items.append(('tasks', 'Tasks', tasks))
        missing = [k for k in (SERVICE_TASK_NAME, RESUME_TASK_NAME) if tasks[k] == 'Missing']
        if missing:
            problems.append(f'{", ".join(missing)} not registered, run wslservice-install-task.bat')

        if tasks[BOOT_TASK_NAME] == 'Running':
            holder = 'task'
        elif windows['keepalive']:
            holder = 'session'
        else:
            holder = None
        items.append(('KEEPALIVE', 'KEEPALIVE', KEEPALIVE))
        items.append(('keepalive_holder', 'Distribution held by', holder))
        if KEEPALIVE and running and holder is None:
            problems.append('KEEPALIVE is enabled but nothing holds the distribution')

        items.append(('restart_shortcut', 'Restart shortcut',
                      str(shortcut.path()) if shortcut.path().exists() else None))

        items.append(('NETWORK_MODE', 'NETWORK_MODE', NETWORK_MODE))
        if NETWORK_MODE == 'mirrored':
            opened = windows['hyperv']
            items.append(('hyperv_firewall_ports', 'Opened on the Hyper-V firewall', opened))
        else:
            address, forwarded = portproxy.get_registgered()
            items.append(('portproxy_address', 'Forwarded to', address))
            items.append(('portproxy_ports', 'Forwarded TCP ports', forwarded))
            if forwarded != sorted(PROXY_FORWARDING_TCP_PORTS):
                problems.append('Forwarded ports differ from the settings, run wslservice.bat')
            opened = advfirewall.get_registgered()
        windows_opened = advfirewall.get_registgered() if NETWORK_MODE == 'mirrored' else opened
        items.append(('windows_firewall_ports', 'Opened on the Windows firewall', windows_opened))
        if opened != FIREWALL_ALLOWED_PORTS:
            problems.append('Opened ports differ from the settings, run wslservice.bat')

        tcp, udp = self.query_listening() if running else (None, None)
        items.append(('listening_tcp_ports', 'Listening inside WSL (TCP)', tcp))
        items.append(('listening_udp_ports', 'Listening inside WSL (UDP)', udp))
        if tcp is not None:
            idle = [v for v in opened if v not in tcp and v not in udp]
            items.append(('opened_without_listener', 'Opened with nothing listening', idle))

        items.append(('resume_log', 'Last resume', self.read_last_line(RESUME_LOG_PATH)))

        return report(items, problems, as_json)

    @classmethod
    def query_windows(self):
        tasks = ', '.join([f"'{v}'" for v in TASK_NAMES])
        resp = powershell(WINDOWS_QUERY.format(tasks=tasks, rule=FIREWALL_RULE_NAME),
                          display_error=False) or ''
        result = {'tasks': {}, 'hyperv': [], 'keepalive': []}
        for line in resp.split('\n'):
            parts = line.strip().split('|')
            if parts[0] == 'task' and len(parts) == 3:
                result['tasks'][parts[1]] = parts[2]
            elif parts[0] == 'hyperv' and len(parts) == 3:
                result['hyperv'] += [int(v) for v in parts[2].split(',') if v.isdigit()]
            elif parts[0] == 'keepalive' and len(parts) == 2:
                result['keepalive'] += [int(parts[1])]
        for name in TASK_NAMES:
            result['tasks'].setdefault(name, 'Missing')
        result['hyperv'] = sorted(set(result['hyperv']))
        return result

    @classmethod
    def query_listening(self):
        resp = execute(bash('ss -Hltn; echo --; ss -Hlun'), display_error=False) or ''
        tcp_lines, _, udp_lines = resp.partition('--')
        return self.parse_ports(tcp_lines), self.parse_ports(udp_lines)

    @classmethod
    def parse_ports(self, lines):
        ports = []
        for line in lines.split('\n'):
            parts = line.split()
            if len(parts) < 4:
                continue
            address, _, port = parts[3].rpartition(':')
            if port.isdigit() and not LOCAL_ADDRESS.match(address):
                ports.append(int(port))
        return sorted(set(ports))

    @classmethod
    def read_last_line(self, path):
        try:
            with open(Path(path), 'rb') as file:
                lines = file.read().decode('utf-8', 'ignore').strip().split('\n')
        except OSError:
            return None
        return lines[-1].strip() if lines else None

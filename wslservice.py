# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import ctypes
import os
import re
import servicemanager
import socket
import subprocess
import sys
import time
import win32event
import win32service
import win32serviceutil
import winreg

from pathlib import Path


# import logging

# logging.basicConfig(
#     filename=Path().resolve().joinpath('wslservice.log'),
#     level=logging.DEBUG,
#     format='[WSL-Init-Service] %(levelname)-7.7s %(message)s'
# )


DISTRIBUTION = 'Ubuntu-20.04'

FIREWALL_RULE_NAME = '+WSL'

FORWARDING_PORTS = [
    22,
    10080,
    18080,
    # SMTP
    587,
    # MariaDB
    3306,
    # Redis
    6379,
    # Elasticsearch
    # 5601,
    # 6443,
    # 9100,
    9200,
    9300,
    # RabbitMQ
    5672,
    15672,
    25672,
    # SMB
    139,
    445,
    # NFS
    111,
    1048,
    2049,
    33333,
    # ChromeDev
    9222,
]

BASH = str(Path('C:/Windows/System32/bash.exe'))
WSL = str(Path('C:/Windows/System32/wsl.exe'))

INITD_SERVICES = [
    'ssh',
    'mysql',
    'redis-server',
    # 'haproxy',
    # 'rabbitmq-server',
    # 'elasticsearch',
    # 'sudo nohup service elasticsearch start >/dev/null 2>&1',
]

# 'bash -c "cd /var/www/home-server && source venv/bin/activate && python manage.py restart"'


INITD_EXECUTES = [
    # 'rm /var/www/home-server/media',
    'sudo ln -fs /mnt/home-server/media /var/www/home-server/media',
    'cd /var/www/home-server && source venv/bin/activate && python manage.py restart',
    # 'cd /var/www/home-server && source venv/bin/activate && nohup python manage.py restart </dev/null >/dev/null 2>&1',
    # 'ping 8.8.8.8 -c 1 -W 1',
]

CWD = os.path.expanduser('~')

DELEGATE_EXEC_REG_KEY = 'DelegateExecute'

ANSI_BACKGROUND_WHITE = '\x1b[7m'
ANSI_RESET = '\x1b[0m'


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
    execute(f'wsl -t {DISTRIBUTION}', shell=True)


def execute(command, shell=False):
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

    if error:
        print(error)
    return resp


class portproxy:

    @classmethod
    def reset(self):
        self.get_registgered()
        execute('netsh interface portproxy reset', shell=True)

    @classmethod
    def showall(self):
        ip, ports = self.get_registgered()
        print()
        print(' * IP Address')
        print(f'   {ip}')
        print()
        print(' * PORTS Opened')
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
                'netsh interface portproxy add v4tov4 '
                'listenport={} listenaddress=0.0.0.0 '
                'connectport={} connectaddress={}').format(
                port, port, wsl_ipaddress), shell=True)

    @classmethod
    def get_wsl_ipaddress(self):
        command = [BASH, '-c', 'ip addr show eth0 | grep "inet\\b" | awk "{print $2}" | cut -d/ -f1']
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=CWD)
        resp, error = proc.communicate()
        resp = re.findall(r'[0-9]+(?:\.[0-9]+){3}', resp)[0]
        # resp = re.findall(r'[0-9]+(?:\.[0-9]+){3}', decode(resp))[0]
        # resp = '127.0.0.1'
        return resp


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
                execute(('{} localport={} name="{}{}" protocol={} dir={}').format(
                    common, ports, FIREWALL_RULE_NAME, protocol, protocol, direction), shell=True)

    @classmethod
    def get_registgered(self):
        ports = []
        for protocol in ('TCP', 'UDP',):
            resp = execute(f'netsh advfirewall firewall show rule name="{FIREWALL_RULE_NAME}{protocol}"', shell=True)
            lines = [v for v in resp.split('\n') if v.startswith('LocalPort:') or v.startswith('RemotePort:')]
            for line in lines:
                line = line.split(':')[-1].strip()
                ports += [int(v) for v in line.split(',') if v.isdigit()]
        return sorted(list(set(ports)))

    @classmethod
    def remove(self):
        self.get_registgered()
        for protocol in ('TCP', 'UDP',):
            execute(f'netsh advfirewall firewall delete rule name="{FIREWALL_RULE_NAME}{protocol}"', shell=True)


class run_as_admin:

    def __init__(self, callback):
        if self.is_admin():
            callback()
        else:
            # self.bypass_uac()
            # self.create_reg_key(DELEGATE_EXEC_REG_KEY, '')
            file = str(Path(__file__).resolve())
            ctypes.windll.shell32.ShellExecuteW(
                None, 'runas', sys.executable, file, None, 1)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def bypass_uac(self, command):
        try:
            self.create_reg_key(DELEGATE_EXEC_REG_KEY, '')
            self.create_reg_key(None, command)
        except WindowsError:
            raise

    def create_reg_key(self, key, value):
        reg_path = 'Software\\Classes\\ms-settings\\shell\\open\\command'
        try:
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, key, 0, winreg.REG_SZ, value)
            winreg.CloseKey(registry_key)
        except WindowsError:
            raise


class initd:

    @classmethod
    def service(self, services):
        prefix = 'sudo nohup service'
        # suffix = '>/dev/null 2>&1'
        suffix = 'restart </dev/null >/dev/null 2>&1'
        _scripts = [f'{prefix} {v} {suffix}' for v in services]
        script = ' && '.join(_scripts)
        resp = execute([BASH, '-c', script])
        if _scripts:
            print(' * SERVICES Started')
            print('   {}'.format(', '.join(services)))
        return resp
        # print(resp)

    @classmethod
    def execute(self, scripts):
        # prefix = 'sudo'
        # _scripts = [f'{prefix} {v}' for v in scripts]
        _scripts = [f'{v}' for v in scripts]
        script = ' && '.join(_scripts)
        resp = execute([BASH, '-c', script])
        if _scripts:
            print(' * SCRIPTS Executed')
            for v in scripts:
                print(f'   {v}')
        return resp


class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = 'WSLInitService'
    _svc_display_name_ = 'WSL Init Service Ubuntu-20.04'

    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.stop_requested = True

    def SvcDoRun(self):
        # self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        main()


def main():
    portproxy.reset()
    advfirewall.remove()
    shutdown()
    advfirewall.add(FORWARDING_PORTS)
    portproxy.add(FORWARDING_PORTS)
    portproxy.showall()
    initd.service(INITD_SERVICES)
    print()
    initd.execute(INITD_EXECUTES)
    print()
    print(' * WSL Service Initialization SUCCESS')
    # print(' ' + ' WSL INITIALIZATION SUCCESS '.join([ANSI_BACKGROUND_WHITE, ANSI_RESET]))
    print()
    time.sleep(1)


if __name__ == '__main__':
    run_as_admin(main)
    # print()
    # win32serviceutil.HandleCommandLine(AppServerSvc)

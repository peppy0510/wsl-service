# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import servicemanager
import socket
import time
import win32event
import win32service
import win32serviceutil

from libadvfirewall import advfirewall
from libbase import execute
from libbase import shutdown
from libinitd import initd
from libportproxy import portproxy
from libuaccontrol import run_as_admin
from settings import ANSI_BACKGROUND_WHITE
from settings import ANSI_RESET
from settings import DISTRIBUTION
from settings import FIREWALL_ALLOWED_PORTS
from settings import INITD_EXECUTES
from settings import INITD_SERVICES
from settings import PROXY_FORWARDING_PORTS
from settings import WSL_EXECUTABLE
# DISTRIBUTION = 'Ubuntu-20.04'

# FIREWALL_RULE_NAME = '+WSL'

# WSL_EXECUTABLE = str(Path('C:/Windows/System32/wsl.exe'))
# BASH_EXECUTABLE = str(Path('C:/Windows/System32/bash.exe'))

# settings = load_commented_json('settings.json')

# INITD_SERVICES = settings.get('INITD_SERVICES')
# INITD_EXECUTES = settings.get('INITD_EXECUTES')

# PROXY_FORWARDING_PORTS = settings.get('PROXY_FORWARDING_PORTS')
# FIREWALL_ALLOWED_PORTS = settings.get('FIREWALL_ALLOWED_PORTS')
# FIREWALL_ALLOWED_PORTS = sorted(list(set(FIREWALL_ALLOWED_PORTS + PROXY_FORWARDING_PORTS)))

# CWD = os.path.expanduser('~')

# DELEGATE_EXEC_REG_KEY = 'DelegateExecute'

# ANSI_BACKGROUND_WHITE = '\x1b[7m'
# ANSI_RESET = '\x1b[0m'


class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = 'WSLService'
    _svc_display_name_ = f'WSL Service {DISTRIBUTION}'

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
    shutdown()
    portproxy.reset()
    advfirewall.remove()

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} -u root '
             'ip addr add 192.168.100.2/24 broadcast 192.168.100.255 '
             'dev eth0 label eth0:1'), display_error=False)
    execute('netsh interface ip add address "vEthernet (WSL)" 192.168.100.3 255.255.255.0')

    print()

    portproxy.add(PROXY_FORWARDING_PORTS)
    portproxy.showall()

    advfirewall.add(FIREWALL_ALLOWED_PORTS)
    advfirewall.showall()

    initd.service(INITD_SERVICES)
    print()
    initd.execute(INITD_EXECUTES)
    # print(' * WSL Service Initialization SUCCESS')
    print(' ' + ' WSL INITIALIZATION SUCCESS '.join([ANSI_BACKGROUND_WHITE, ANSI_RESET]))
    print()
    time.sleep(1)


if __name__ == '__main__':
    run_as_admin(main)
    # print()
    # win32serviceutil.HandleCommandLine(AppServerSvc)

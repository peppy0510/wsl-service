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
from settings import BINDING_ADDRESS
from settings import BROADCAST_ADDRESS
from settings import DISTRIBUTION
from settings import FIREWALL_ALLOWED_PORTS
from settings import INITD_EXECUTES
from settings import INITD_SERVICES
from settings import PROXY_FORWARDING_PORTS
from settings import VETHERNET_ADDRESS
from settings import WSL_EXECUTABLE


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
             f'ip addr del {BINDING_ADDRESS}/24'
             'dev eth0 label eth0:1'), display_error=False)

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} -u root '
             f'ip addr add {BINDING_ADDRESS}/24 broadcast {BROADCAST_ADDRESS} '
             'dev eth0 label eth0:1'), display_error=False)

    execute(f'netsh interface ip add address "vEthernet (WSL)" {VETHERNET_ADDRESS} 255.255.255.0')

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

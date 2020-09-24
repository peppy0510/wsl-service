# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import socket

import servicemanager
import win32event
import win32service
import win32serviceutil

from settings import DISTRIBUTION


class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = 'WSLService'
    _svc_display_name_ = f'WSL Service {DISTRIBUTION}'

    def __init__(self, *args):

        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False

    def SvcStop(self):
        import win32event
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
        from wslservice import main
        main()

# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import argparse
import asyncio
import time

from libadvfirewall import advfirewall
from libbase import execute
from libbase import shutdown
from libinitd import initd
from libportproxy import portproxy
from libuaccontrol import run_as_admin
from powershell import patch_powershell_history
from settings import ANSI_BACKGROUND_WHITE
from settings import ANSI_RESET
from settings import BINDING_ADDRESS
from settings import BROADCAST_ADDRESS
from settings import DISTRIBUTION
from settings import FIREWALL_ALLOWED_PORTS
from settings import INITD_DISALLOWED_SERVICES
from settings import INITD_EXECUTES
from settings import INITD_SERVICES
from settings import PROXY_FORWARDING_TCP_PORTS
from settings import VETHERNET_ADDRESS
from settings import WSL_EXECUTABLE


ENABLE_INITD = True
ENABLE_NETWORK = True
PATCH_POWERSHELL_HISTORY = False


parser = argparse.ArgumentParser(prog='python wslservice.py', add_help=True)

parser.add_argument(
    '-n',
    '--network_only',
    action='store_true',
    help='network only',
)

parser.add_argument(
    '-i',
    '--initd_only',
    action='store_true',
    help='initd only',
)

args = parser.parse_args()

ENABLE_INITD = False if args.network_only else ENABLE_INITD
ENABLE_NETWORK = False if args.initd_only else ENABLE_NETWORK


def setup_network_inside_wsl():

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} -u root '
             f'ip addr del {BINDING_ADDRESS}/24 '
             'dev eth0 label eth0:1'), display_error=False)

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} -u root '
             f'ip addr add {BINDING_ADDRESS}/24 broadcast {BROADCAST_ADDRESS} '
             'dev eth0 label eth0:1'), display_error=False)


def launch_dbus_wsl():

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} '
             f'--exec dbus-launch true'), display_error=False)


async def aiomain():
    if ENABLE_NETWORK:
        shutdown()
        launch_dbus_wsl()
        portproxy.reset()
        advfirewall.remove()

        # setup_network_inside_wsl()

        # execute((f'netsh interface ip add address '
        #          f'"vEthernet (WSL)" {VETHERNET_ADDRESS} 255.255.255.0'))

        # execute((f'netsh interface ip add address '
        #          f'"vEthernet (WSLCore)" {VETHERNET_ADDRESS} 255.255.255.0'))

        # execute((f'netsh interface ip add address '
        #          f'"vEthernet (WSL (Hyper-V firewall))" {VETHERNET_ADDRESS} 255.255.255.0'))

        print()

        portproxy.add(PROXY_FORWARDING_TCP_PORTS)
        portproxy.showall()

        advfirewall.add(FIREWALL_ALLOWED_PORTS)
        advfirewall.showall()

    if ENABLE_INITD:
        if not ENABLE_NETWORK:
            shutdown()
            launch_dbus_wsl()
            setup_network_inside_wsl()

        # print()
        time.sleep(5)
        # await initd.systemd(INITD_SERVICES, INITD_DISALLOWED_SERVICES, concurrent=False)
        # await initd.service(INITD_SERVICES, concurrent=False)
        print()
        initd.execute(INITD_EXECUTES)
        print() if INITD_EXECUTES else None
        print(' ' + ' WSL INITIALIZATION SUCCESS '.join([ANSI_BACKGROUND_WHITE, ANSI_RESET]))
        print()
        time.sleep(1)

    if PATCH_POWERSHELL_HISTORY:
        patch_powershell_history()


def main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(aiomain())
    loop.close()


if __name__ == '__main__':
    if args.initd_only:
        main()
    else:
        run_as_admin(main)
    # win32serviceutil.HandleCommandLine(AppServerSvc)

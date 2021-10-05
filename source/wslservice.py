# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import asyncio
import time

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
from settings import PROXY_FORWARDING_TCP_PORTS
from settings import VETHERNET_ADDRESS
from settings import WSL_EXECUTABLE


async def aiomain():
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

    portproxy.add(PROXY_FORWARDING_TCP_PORTS)
    portproxy.showall()

    advfirewall.add(FIREWALL_ALLOWED_PORTS)
    advfirewall.showall()

    print()
    await initd.systemd(INITD_SERVICES)
    # await initd.service(INITD_SERVICES)
    print()
    initd.execute(INITD_EXECUTES)
    print() if INITD_EXECUTES else None
    print(' ' + ' WSL INITIALIZATION SUCCESS '.join([ANSI_BACKGROUND_WHITE, ANSI_RESET]))
    print()
    time.sleep(1)


def main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(aiomain())
    loop.close()


if __name__ == '__main__':
    run_as_admin(main)
    # win32serviceutil.HandleCommandLine(AppServerSvc)

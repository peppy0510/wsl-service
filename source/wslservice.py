# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import argparse
import asyncio
import subprocess
import sys
import time

from libadvfirewall import advfirewall
from libbase import distributions
from libbase import execute
from libbase import shutdown
from libcheck import check
from libhypervfirewall import hypervfirewall
from libinitd import initd
from libportproxy import portproxy
from libresume import resume
from libschtasks import schtasks
from libshortcut import shortcut
from libstatus import status
from libuaccontrol import is_admin
from libuaccontrol import run_as_admin
from settings import ANSI_BACKGROUND_WHITE
from settings import ANSI_RESET
from settings import BINDING_ADDRESS
from settings import BOOT_TASK_NAME
from settings import BROADCAST_ADDRESS
from settings import DISTRIBUTION
from settings import FIREWALL_ALLOWED_PORTS
from settings import INITD_EXECUTES
from settings import KEEPALIVE
from settings import NETWORK_MODE
from settings import PROXY_FORWARDING_TCP_PORTS
from settings import RESUME_ACTION
from settings import VETHERNET_ADDRESS
from settings import WSL_EXECUTABLE


ENABLE_INITD = True
ENABLE_NETWORK = True


parser = argparse.ArgumentParser(prog='python.exe wslservice.py', add_help=True)

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

parser.add_argument(
    '-r',
    '--resume',
    action='store_true',
    help='recover after the host resumed from sleep',
)

parser.add_argument(
    '--install_task',
    action='store_true',
    help='register the scheduled tasks',
)

parser.add_argument(
    '--uninstall_task',
    action='store_true',
    help='remove the scheduled tasks',
)

parser.add_argument(
    '-c',
    '--check',
    action='store_true',
    help='print the resolved settings and check them without changing anything',
)

parser.add_argument(
    '-s',
    '--status',
    action='store_true',
    help='print what is running and what is opened right now without changing anything',
)

parser.add_argument(
    '--json',
    action='store_true',
    help='print --check or --status as json',
)

parser.add_argument(
    '--restart',
    action='store_true',
    help='restart the distribution, elevated only when the network mode needs it',
)

args = parser.parse_args()

# Firewall rules survive a restart in mirrored mode, so it needs neither the network part nor
# elevation.
RESTART_UNELEVATED = args.restart and NETWORK_MODE == 'mirrored'

ENABLE_INITD = False if args.network_only else ENABLE_INITD
ENABLE_NETWORK = False if args.initd_only or RESTART_UNELEVATED else ENABLE_NETWORK


def setup_network_inside_wsl():

    if BINDING_ADDRESS == resume.default_field('via'):
        print(f' * BINDING_ADDRESS {BINDING_ADDRESS} is the gateway of the distribution')
        print()
        return

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} -u root '
             f'ip addr del {BINDING_ADDRESS}/24 '
             'dev eth0 label eth0:1'), display_error=False)

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} -u root '
             f'ip addr add {BINDING_ADDRESS}/24 broadcast {BROADCAST_ADDRESS} '
             'dev eth0 label eth0:1'), display_error=False)


def launch_dbus_wsl():

    execute((f'{WSL_EXECUTABLE} -d {DISTRIBUTION} '
             f'--exec dbus-launch true'), display_error=False)


def stop_distribution():
    shutdown()
    deadline = time.time() + 30
    while DISTRIBUTION in distributions(running=True) and time.time() < deadline:
        time.sleep(0.5)


def start_keepalive():
    if not KEEPALIVE:
        return
    if is_admin() and schtasks.run(BOOT_TASK_NAME):
        return
    # Without elevation the boot task cannot be started, so this logon session holds the
    # distribution until the task takes over again on the next boot.
    subprocess.Popen(
        ['conhost.exe', '--headless', WSL_EXECUTABLE, '-d', DISTRIBUTION, '-u', 'root',
         '--', 'sleep', 'infinity'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True)


async def aiomain():
    if args.uninstall_task:
        schtasks.uninstall()
        shortcut.remove()
        schtasks.showall()
        shortcut.show()
        return

    if args.install_task:
        schtasks.install()
        shortcut.create()
        schtasks.showall()
        shortcut.show()
        return

    restart = NETWORK_MODE != 'mirrored'

    if args.restart:
        stop_distribution()
        start_keepalive()
        restart = False

    if args.resume:
        if RESUME_ACTION == 'none':
            return
        if RESUME_ACTION == 'heal' and resume.heal():
            return
        restart = True

    if ENABLE_NETWORK:
        if restart:
            shutdown()

        launch_dbus_wsl()

        if NETWORK_MODE == 'mirrored':
            portproxy.reset()

            print()

            hypervfirewall.add(FIREWALL_ALLOWED_PORTS)
            hypervfirewall.showall()

        else:
            hypervfirewall.remove()
            portproxy.reset()
            advfirewall.remove()

            setup_network_inside_wsl()

            execute((f'netsh interface ip add address '
                     f'"vEthernet (WSL)" {VETHERNET_ADDRESS} 255.255.255.0'), display_error=False)

            execute((f'netsh interface ip add address '
                     f'"vEthernet (WSLCore)" {VETHERNET_ADDRESS} 255.255.255.0'), display_error=False)

            execute((f'netsh interface ip add address '
                     f'"vEthernet (WSL (Hyper-V firewall))" {VETHERNET_ADDRESS} '
                     f'255.255.255.0'), display_error=False)

            print()

            portproxy.add(PROXY_FORWARDING_TCP_PORTS)
            portproxy.showall()

        advfirewall.add(FIREWALL_ALLOWED_PORTS)
        advfirewall.showall()

    if ENABLE_INITD:
        if not ENABLE_NETWORK:
            if restart:
                shutdown()
            launch_dbus_wsl()
            if NETWORK_MODE != 'mirrored':
                setup_network_inside_wsl()

        time.sleep(5)
        print()
        initd.execute(INITD_EXECUTES)
        print() if INITD_EXECUTES else None
        print(' ' + ' WSL INITIALIZATION SUCCESS '.join([ANSI_BACKGROUND_WHITE, ANSI_RESET]))
        print()
        time.sleep(1)

    if args.restart:
        print(' * DISTRIBUTIONS Running')
        print(f'   {", ".join(distributions(running=True)) or "none"}')
        print()
        time.sleep(3)


def main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(aiomain())
    loop.close()


if __name__ == '__main__':
    if args.check:
        sys.exit(check.run(args.json))
    elif args.status:
        sys.exit(status.run(args.json))
    elif args.initd_only or RESTART_UNELEVATED:
        main()
    else:
        run_as_admin(main)

# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import asyncio
import re
import time

from libbase import aioexecute
from libbase import execute
from pathlib import Path
from settings import BASH_EXECUTABLE
from settings import DISTRIBUTION

SYSTEMD_EXCLUDES = [
    'acpid',
    'anacron',
    'irqbalance',
    'kerneloops',
    'sddm',
    'whoopsie',
    'xrdp',
]

SERVICES_INCLUDES = [
    'redis-server',
]


class initd:

    @classmethod
    def get_systemd_services(self):
        resp = execute([BASH_EXECUTABLE, 'service', '--status-all'], display_error=False)
        lines = [v.strip() for v in resp.split('\n')]
        lines = [v for v in lines if v]

        services = SERVICES_INCLUDES

        for line in lines:
            matched = re.match(r'^\[\s([\+\-\?])\s\][\s]{1,}([a-zA-Z\.]{1,})$', line)
            if matched:
                name = matched.group(2)
                services += [name]

        services = sorted(list(set(services)))

        systemds = []

        for root in ['/etc/systemd/system', '/etc/systemd/system/multi-user.target.wants']:
            for path in sorted(Path(f'\\\\wsl$\\{DISTRIBUTION}').joinpath(root).glob('*.service')):
                if path.is_file():
                    systemds += [path.stem]

        systemds = sorted(list(set(systemds)))

        for i in range(len(services) - 1, -1, -1):
            if services[i] not in systemds:
                services.pop(i)
                continue
            if services[i] in SYSTEMD_EXCLUDES:
                services.pop(i)
                continue

        return services

    @classmethod
    async def systemd(self, services=[], concurrent=False):
        services += self.get_systemd_services()
        services = sorted(list(set(services)))
        await self.service(services, concurrent=concurrent)

    @classmethod
    async def service(self, services, concurrent=True):
        if not services:
            return ''
        prefix = 'sudo nohup service'
        # suffix = '>/dev/null 2>&1'
        suffix = 'restart </dev/null >/dev/null 2>&1'
        _scripts = [f'{prefix} {v} {suffix}' for v in services]

        if concurrent:
            resps = await asyncio.gather(*[aioexecute([
                BASH_EXECUTABLE, '-c', v]) for v in _scripts])
            resp = b''.join(resps)

        else:
            resp = execute([BASH_EXECUTABLE, '-c', ' && '.join(_scripts)])

        if _scripts:
            print(' * SERVICES Started')
            print('   {}'.format(', '.join(services)))

        return resp

    @classmethod
    def execute(self, scripts):
        if not scripts:
            return ''
        # prefix = 'sudo'
        # _scripts = [f'{prefix} {v}' for v in scripts]
        _scripts = [f'{v}' for v in scripts]
        script = ' && '.join(_scripts)
        resp = execute([BASH_EXECUTABLE, '-c', script])
        if _scripts:
            print(' * SCRIPTS Executed')
            for v in scripts:
                print(f'   {v}')
        return resp

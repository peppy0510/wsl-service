# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import sys
import tempfile

from libbase import execute
from libbase import powershell
from pathlib import Path
from settings import BOOT_TASK_NAME
from settings import DISTRIBUTION
from settings import KEEPALIVE
from settings import PROJECT_PATH
from settings import RESUME_TASK_NAME
from settings import SERVICE_TASK_NAME


TASK_TEMPLATE = '''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Author>{author}</Author>
    <Description>{description}</Description>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>{user_id}</UserId>
      <LogonType>S4U</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>{execution_time_limit}</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <Hidden>true</Hidden>
  </Settings>
  <Triggers>
{trigger}
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{working_directory}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''

IDENTITY_COMMAND = ('$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent(); '
                    '$identity.Name; $identity.User.Value')

BOOT_TRIGGER = '    <BootTrigger />'

RESUME_TRIGGER = '''    <EventTrigger>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="System"&gt;&lt;Select Path="System"&gt;\
*[System[Provider[@Name='Microsoft-Windows-Power-Troubleshooter'] and EventID=1]]\
&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
      <Delay>PT10S</Delay>
    </EventTrigger>'''


class schtasks:

    @classmethod
    def install(self):
        author, user_id = self.identity()
        script = str(Path(PROJECT_PATH).joinpath('source', 'wslservice.py'))

        self.create(SERVICE_TASK_NAME, TASK_TEMPLATE.format(
            author=author,
            user_id=user_id,
            description='Starts WSL networking and the init commands on boot.',
            execution_time_limit='PT10M',
            trigger=BOOT_TRIGGER,
            command=sys.executable,
            arguments=f'"{script}"',
            working_directory=PROJECT_PATH))

        self.create(RESUME_TASK_NAME, TASK_TEMPLATE.format(
            author=author,
            user_id=user_id,
            description='Recovers WSL networking on system resume.',
            execution_time_limit='PT10M',
            trigger=RESUME_TRIGGER,
            command=sys.executable,
            arguments=f'"{script}" --resume',
            working_directory=PROJECT_PATH))

        if not KEEPALIVE:
            self.delete(BOOT_TASK_NAME)
            return

        self.create(BOOT_TASK_NAME, TASK_TEMPLATE.format(
            author=author,
            user_id=user_id,
            description='Keeps the WSL distribution running without a user logon.',
            execution_time_limit='PT0S',
            trigger=BOOT_TRIGGER,
            command='conhost.exe',
            arguments=f'--headless wsl.exe -d {DISTRIBUTION} -u root -- sleep infinity',
            working_directory=PROJECT_PATH))

    @classmethod
    def identity(self):
        resp = (powershell(IDENTITY_COMMAND) or '').split()
        return resp if len(resp) == 2 else ['', '']

    @classmethod
    def uninstall(self):
        self.delete(SERVICE_TASK_NAME)
        self.delete(RESUME_TASK_NAME)
        self.delete(BOOT_TASK_NAME)

    @classmethod
    def create(self, name, xml):
        path = Path(tempfile.gettempdir()).joinpath(f'{name}.xml')
        with open(path, 'wb') as file:
            file.write(xml.encode('utf-16'))
        execute(f'schtasks /Create /TN "{name}" /XML "{path}" /F', shell=True)
        path.unlink(missing_ok=True)

    @classmethod
    def delete(self, name):
        execute(f'schtasks /Delete /TN "{name}" /F', shell=True, display_error=False)

    @classmethod
    def showall(self):
        print(' * TASKS Registered')
        for name in (SERVICE_TASK_NAME, RESUME_TASK_NAME, BOOT_TASK_NAME,):
            resp = execute(f'schtasks /Query /TN "{name}"', shell=True, display_error=False)
            print(f'   {name}: {"yes" if resp and name in resp else "no"}')
        print()

# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


from pathlib import Path
from settings import DISTRIBUTION


def patch_powershell_history():
    path = Path(f'//wsl.localhost/{DISTRIBUTION}').joinpath(
        'root/.local/share/powershell/PSReadLine/ConsoleHost_history.txt')
    if not path.exists():
        return
    linesep = '\n'
    with open(path, 'rb') as file:
        content = file.read().decode('utf-8')
    removes = []
    lines = content.split(linesep)
    for i in range(len(lines) - 1, -1, -1):
        if '�' in lines[i]:
            removes += [lines.pop(i)]
    if not removes:
        return
    content = linesep.join(lines)
    with open(path, 'wb') as file:
        file.write(content.encode('utf-8'))

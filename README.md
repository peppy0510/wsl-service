# WSL Service

> Maintenance only. [PyWinSystem](https://github.com/peppy0510/PyWinSystem) does all of this
> with a window to edit the settings, `.wslconfig` and `/etc/wsl.conf`, a tray menu, and the
> same from the command line. `PyWinSystem.exe --wsl migrate` moves your settings over and
> removes what this tool registered; see "Coming from wsl-service" in its README. This
> repository keeps working and gets fixes, but no new features.

* Starts your WSL distribution on Windows boot, before anyone logs on.
* Publishes WSL ports to your network and opens them on the Windows firewall.
* Runs init commands, so a web server comes up like a Linux daemon.
* Restores WSL networking after the host wakes from sleep.
* Everything is configured in one json file.

## Requirements

* Windows 10 or Windows 11 with WSL 2.
* Python 3 for Windows.
* The `mirrored` network mode additionally requires Windows 11 22H2 or later with WSL 2.0 or
  later, because it opens ports through the Hyper-V firewall, which Windows 10 does not have.

## How to use

* Download or clone this repository.
* Create `settings.json` in the repository root, see [Your own configuration](#your-own-configuration).
* Run `wslservice-check.bat` and fix every problem it reports.
* Run `wslservice.bat` once to check that it works on your machine.
* Register the scheduled tasks with `wslservice-install-task.bat`.

## First setup

Everything except the last two steps reads the machine without changing it, so it is safe to run
again and again.

1. `wsl.exe -l -v` lists the installed distributions. Put the exact name into `DISTRIBUTION`.
2. Look up `networkingMode` in `%USERPROFILE%\.wslconfig`. `mirrored` there means
   `"NETWORK_MODE": "mirrored"`, anything else or nothing means `portproxy`.
3. List what listens inside WSL with `ss -ltnp` and `ss -lunp`. Every port in the port lists is
   reachable from the LAN, so keep only what other machines have to reach. The defaults include
   databases and many services you probably do not run.
4. Write only the keys that differ from `source/settings.json` into your own `settings.json`.
5. Run `wslservice-check.bat`, or `python.exe source/wslservice.py --check` from a WSL shell inside
   the repository. It prints the resolved settings and the ports that will be opened, checks them
   against the machine, and exits with 1 when something has to be fixed. It needs no elevation.
6. Run `wslservice.bat` elevated. It asks for elevation itself and then applies everything.
7. Run `wslservice-install-task.bat` elevated.
8. Run `wslservice-status.bat` to see that it all took effect.

## Status

`wslservice-status.bat`, or `python.exe source/wslservice.py --status`, prints what is in effect
right now without changing anything and without elevation: whether the distribution runs, the
state of the tasks, what holds the distribution for `KEEPALIVE`, the ports opened on the firewalls
or forwarded, the ports listening inside WSL, and the last resume. It exits with 1 when the
settings have not been applied yet. When WSL is not running it does not start it, so the
listening ports stay empty.

Add `--json` to `--check` or `--status` for output that other programs can read. `--check --json`
also carries the sections and keys of `.wslconfig`.

## How to register

Run the installer from an elevated prompt. It writes the task definitions itself, so neither NSSM
nor NirCmd is needed, and it replaces whatever it registered before.

```bash
wslservice-install-task.bat
```

Remove the tasks again with the matching script.

```bash
wslservice-uninstall-task.bat
```

The tasks run as the current user with the highest available privileges, without a window and
without a logon. Running them as `SYSTEM` would start a WSL instance of its own, so it is not an
option.

| Task | Trigger | What it does |
| --- | --- | --- |
| `WSLService` | Boot | Publishes the ports and runs the init commands. |
| `WSL-Resume` | Resume from sleep, delayed 10s | Applies `RESUME_ACTION`. |
| `WSL-Boot` | Boot, and a WSL update installed, delayed 30s | Holds the distribution running. Registered when `KEEPALIVE` is enabled. |

`wslservice-run-task.bat` runs the registered `WSLService` task on demand.

## Restarting WSL

The installer also adds a `WSL Restart` shortcut to the Start menu, and the uninstaller removes it.
`wslservice-restart.bat` does the same from the repository. Use it when the distribution is stuck.

It shuts WSL down, starts `KEEPALIVE` again and runs `INITD_EXECUTES`. In `mirrored` mode the
firewall rules survive a restart, so it runs without elevation, and `KEEPALIVE` is held by your
logon session until the `WSL-Boot` task takes over again on the next boot. In `portproxy` mode the
forwarding has to be written again for the new WSL address, so it asks for elevation.

## Network modes

`NETWORK_MODE` selects how WSL is published to the host and to the LAN.

* `portproxy` (default): WSL keeps its own address behind the NAT switch, and the host publishes it
  with `netsh interface portproxy`. The address changes on every WSL start, so the service restarts
  the distribution and rewrites the forwarding rules.
* `mirrored`: WSL shares the host network adapters, which requires `networkingMode=mirrored` in
  `%USERPROFILE%\.wslconfig`. Port forwarding no longer applies, so inbound ports are opened on the
  Hyper-V firewall of the WSL virtual machine instead, and the distribution is not restarted.

```ini
[wsl2]
networkingMode=mirrored
```

## Recovery after sleep

WSL networking often does not survive a host sleep. `RESUME_ACTION` selects what happens when the
`WSL-Resume` task fires.

* `restart` (default): restart the distribution, exactly like a normal service start.
* `heal`: probe the distribution, its outbound networking and its inbound ports, then repair only
  the layer that failed. A restart is the fallback when the repair does not bring everything back.
  Every probe is appended to `RESUME_LOG_PATH`.
* `none`: do nothing.

Repairing the network takes the mirrored interface down and up, which disconnects WSL for a few
seconds and can renumber the interfaces, so `eth1` may come back as `eth0`. Nothing inside WSL
should hold on to an interface name across a resume.

## Your own configuration

`source/settings.json` holds the defaults. Your own `settings.json` in the repository root only
needs the keys you change. Every key set there replaces the default value as a whole, so a port
removed from a list stays closed. Keys left out keep their defaults.

* Comments are whole lines starting with `//`. A comment after a value on the same line breaks
  the file.
* A value must keep the type of its default, a list stays a list and `KEEPALIVE` stays `true` or
  `false`. Anything else stops with an error naming the key.

Every port in `PROXY_FORWARDING_TCP_PORTS`, `PROXY_FORWARDING_UDP_PORTS`,
`SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS` and `FIREWALL_ALLOWED_PORTS` is opened on the
Windows firewall, and in `mirrored` mode on the Hyper-V firewall as well. In `mirrored` mode
nothing is forwarded, so the forwarding lists only decide which ports are opened.

* `DISTRIBUTION`: Name of the distribution exactly as `wsl.exe -l -v` prints it.
* `NETWORK_MODE`: `portproxy` or `mirrored`, see above. It has to match `networkingMode` in
  `.wslconfig`.
* `EXTERNAL_ADDRESS`: Host address the ports are published on. Empty picks the address of the
  adapter that holds the default route.
* `BINDING_ADDRESS`: Static local ip address for your WSL, `portproxy` mode only. It must stay
  outside the subnet of your LAN, otherwise it collides with your router and breaks routing inside
  WSL.
* `VETHERNET_ADDRESS`: Address given to the host side `vEthernet (WSL)` adapters, `portproxy`
  mode only.
* `PROXY_FORWARDING_TCP_PORTS`: Ports forwarded from the host to WSL with `netsh interface
  portproxy`.
* `PROXY_FORWARDING_UDP_PORTS`: Ports relayed from the host to WSL by `wsludpservice.bat`, which
  is not registered as a task and has to be started on its own. `portproxy` mode only.
* `SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS`: Same as above, but every relayed packet is
  prefixed with the sender as `host:port`, for a server inside WSL that needs to know who sent it.
* `FIREWALL_ALLOWED_PORTS`: Extra ports opened on the firewall without forwarding, such as a
  reverse proxy running on Windows.
* `INITD_EXECUTES`: Commands run with bash inside `DISTRIBUTION` at start, such as your own
  server. Services such as ssh, nginx or mysql are better enabled with systemd inside WSL.
* `HYPERV_VM_CREATOR_ID`: Id of the WSL virtual machine for the Hyper-V firewall. The default is
  the id WSL registers, so leave it out.

A key that is not in `source/settings.json` does nothing, and `wslservice-check.bat` reports it.
* `RESUME_ACTION`: `restart`, `heal` or `none`, see above.
* `RESUME_PROBE_HOST`: Optional hostname resolved inside WSL. Left empty, outbound networking is
  judged by the presence of the default route alone, which needs no network of its own.
* `RESUME_PROBE_PORTS`: Ports connected from the host to probe inbound networking. Something
  inside WSL has to listen on them, otherwise every resume looks like a failure.
* `RESUME_LOG_PATH`: Where the probe results are appended.
* `KEEPALIVE`: Keeps the distribution running from boot without a user logon.

## Reference

* Accessing network applications with WSL
    - https://learn.microsoft.com/en-us/windows/wsl/networking
* Advanced settings configuration in WSL
    - https://learn.microsoft.com/en-us/windows/wsl/wsl-config

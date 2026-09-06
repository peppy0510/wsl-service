# WSL Service

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
* Copy `source/settings.json` to the repository root and edit your own settings.
* Run `wslservice.bat` once to check that it works on your machine.
* Register the scheduled tasks with `wslservice-install-task.bat`.

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
| `WSL-Boot` | Boot | Holds the distribution running. Registered when `KEEPALIVE` is enabled. |

`wslservicetask.bat` runs the registered `WSLService` task on demand.

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

`source/settings.json` holds the defaults. Copy it to the repository root and edit that copy,
which is merged over the defaults.

* `EXTERNAL_ADDRESS`: Host address the ports are published on. Empty picks the address of the
  adapter that holds the default route.
* `BINDING_ADDRESS`: Static local ip address for your WSL. It must stay outside the subnet of
  your LAN, otherwise it collides with your router and breaks routing inside WSL.
* `VETHERNET_ADDRESS`: Address given to the host side `vEthernet (WSL)` adapters, `portproxy`
  mode only.
* `FIREWALL_ALLOWED_PORTS`: Ports opened on the Windows firewall.
* `PROXY_FORWARDING_TCP_PORTS`: Ports forwarded from the host to WSL.
* `INITD_SERVICES`: Services started inside WSL, such as ssh, nginx, mysql or redis.
* `INITD_EXECUTES`: Commands run inside WSL after the services, such as your own server.
* `NETWORK_MODE`: `portproxy` or `mirrored`, see above.
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

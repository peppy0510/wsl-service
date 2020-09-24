## WSL Service

Helps WSL(Windows Subsystem for Linux) startup on you Windows boot.
You can configure with `settings.json` file.

* `FIREWALL_ALLOWED_PORTS`: Automatic registeration on Windows firewall allowed port
* `PROXY_FORWARDING_PORTS`: Automatic registeration on Windows proxy port forwarding
* `INITD_SERVICES`: Automatically executes startup services such as ssh, nginx, mysql, redis, ...
* `INITD_EXECUTES`: Automatically executes additional commands on startup such as your own server.

## How to register as Windows Service

#### To Install as Windows Service

1. Install NSSM(Non-Sucking Service Manager)
    * Download form https://nssm.cc/ or install with `choco install nssm`

2. Register `wslservice.bat` as windows service with oneshot mode and logon with your account

```bash
nssm.exe install WSLService
```

#### To Remove from Windows Service

```bash
nssm.exe remove WSLService
```

# author: Taehong Kim
# email: peppy0510@hotmail.com

# wsl --terminate Ubuntu-20.04

PROXY_PORTS=("22" "23" "587" "3306" "6379" "15672" "25672")
FIREWALL_PORTS=("22" "23" "80" "443" "587" "3306" "6379" "8000" "8080" "8443" "10080" "18080" "15672" "25672")

WSL="C:\\Windows\System32\\wsl.exe"
BASH="C:\\Windows\\System32\\bash.exe"

${BASH} -c "sudo nohup service ssh start </dev/null >/dev/null 2>&1"
${BASH} -c "sudo nohup service mysql start </dev/null >/dev/null 2>&1"
${BASH} -c "sudo nohup service redis-server start </dev/null >/dev/null 2>&1"
${BASH} -c "cd /var/www/fdreplay-server && source venv/bin/activate && python manage.py restart"

${WSL} -d Ubuntu-20.04 -u root ip addr add 192.168.100.2/24 broadcast 192.168.100.255 dev eth0 label eth0:1
netsh interface ip add address "vEthernet (WSL)" 192.168.100.3 255.255.255.0

netsh advfirewall firewall delete rule name="+WSLTCP"
netsh advfirewall firewall delete rule name="+WSLUDP"

FIREWALL_PORTS=$(printf ",%s" "${FIREWALL_PORTS[@]}")
FIREWALL_PORTS=${FIREWALL_PORTS:1}

netsh advfirewall firewall add rule action=allow localport=${FIREWALL_PORTS} name="+WSLTCP" protocol=TCP dir=in
netsh advfirewall firewall add rule action=allow localport=${FIREWALL_PORTS} name="+WSLTCP" protocol=TCP dir=out
netsh advfirewall firewall add rule action=allow localport=${FIREWALL_PORTS} name="+WSLUDP" protocol=UDP dir=in
netsh advfirewall firewall add rule action=allow localport=${FIREWALL_PORTS} name="+WSLUDP" protocol=UDP dir=out

netsh interface portproxy reset

for ((i=0; i<=${#PROXY_PORTS[@]}; i++)); do
    port=${PROXY_PORTS[${i}]}
    netsh interface portproxy add v4tov4 \
        listenaddress=0.0.0.0 listenport=${port} \
        connectaddress=192.168.100.2 connectport=${port}
done

# sleep 10

netsh interface portproxy show all

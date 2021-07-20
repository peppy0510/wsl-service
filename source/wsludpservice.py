# encoding: utf-8


'''
author: Taehong Kim
email: peppy0510@hotmail.com
'''


import asyncio
import socket
import threading

from settings import BINDING_ADDRESS
from settings import PROXY_FORWARDING_UDP_PORTS
from settings import SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS


class WSLUDPService(threading.Thread):
    def __init__(
        self,
        src_host='0.0.0.0',
        dst_host=BINDING_ADDRESS,
        port=50002,
        insert_source=False,
    ):
        self.port = port
        self.src_host = src_host
        self.dst_host = dst_host
        self.insert_source = insert_source
        self.queue = []
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dst_socket:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as src_sock:
                src_sock.bind((self.src_host, self.port))
                while True:
                    # data, (src_host, port) = src_sock.recvfrom(8192)
                    data, (src_host, port) = src_sock.recvfrom(4096)

                    print((src_host, port,), data)

                    if src_host == self.dst_host:
                        continue

                    if self.insert_source:
                        data = f'{src_host}:{port}'.encode('utf-8') + data

                    dst_socket.sendto(data, (self.dst_host, self.port))


async def aiomain():
    [
        WSLUDPService(port=port, insert_source=False).start()
        for port in PROXY_FORWARDING_UDP_PORTS
    ]
    [
        WSLUDPService(port=port, insert_source=True).start()
        for port in SOURCE_INSERTED_PROXY_FORWARDING_UDP_PORTS
    ]

    while True:
        await asyncio.sleep(0.1)


def main():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(aiomain())
        loop.close()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()

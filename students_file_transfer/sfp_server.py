'''
sfp_server.py

Students File Protocol server implementation.
Using:
    socket
    threading
    select

Protocol is defined in README.md of this directory.
'''

import socket
import os
import logging
import argparse
import sys
from collections import defaultdict
import select
import threading
from typing import Dict

__author__ == 'Giulio Corradini'

class SFPProtocolResponder:
    MESSAGE_PROCESSING_COMPLETE = 0
    MESSAGE_INCOMPLETE = 1

    def __init__(self, buffer: bytearray, lock: threading.Lock):
        self.buffer = buffer
        self.lock = lock
        self.state = SFPProtocolResponder.MESSAGE_PROCESSING_COMPLETE

    def decodeProtocol(self, ingoing: bytearray):
        '''
        Decodes a message from the buffer. The responder is stateful, every
        thread should istantiate its own.
        :param ingoing: socket ingoing buffer as bytearray
        :return: 0 is a full message has been processed
        1 if the incoming message is incomplete. The lower layer may call recv
        Remaining bytes to request to process current message
        '''
        if self.state == SFPProtocolResponder.MESSAGE_PROCESSING_COMPLETE:
            return
        return


class ClientConnection(threading.Thread):
    CLIENT_NUMBER = 0

    def __init__(self, conn: socket.socket):
        self.name = "Client{}".format(ClientConnection.CLIENT_NUMBER)
        ClientConnection.CLIENT_NUMBER += 1

        self.conn = conn
        self.conn.setblocking(False)

        #L3 to L4 IPC
        self.buffer_lock = threading.Lock()
        self.buffer = bytearray()

        #L4 SAP
        self.new_data_available = threading.Condition()
        self.protocol_session = SFPProtocolResponder(self.buffer, self.buffer_lock)

    def recv(self, bufsize, flags=0) -> bytes:
        data = self.conn.recv(bufsize, flags)
        with self.new_data_available:
            self.buffer += data
            self.new_data_available.notify()

        return data

    def send(self, bytes: bytes, flags=0) -> int:
        return self.conn.send(bytes, flags)

    def run(self):
        while True:




def main(host, port):
    '''
    Front desk. Manages the registration of clients.
    :param host: host to bind the listening socket to
    :param port: port to listen to
    :return:
    '''

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as frontdesk_sock:
        s.bind((host, port))
        s.listen(5)
        s.setblocking(False)

        active_socks = [s]
        clients: Dict[socket.socket, ClientConnection] = {}

        while not shutdown.is_set():
            readable, writable, exceptions = select.select(active_socks, None, active_socks, timeout=10)
            for sock in readable:

                if sock is frontdesk_sock:
                    conn, addr = sock.accept()
                    cl = ClientConnection(conn)
                    clients[conn] = nc
                    active_socks.append(conn)

                else:
                    cl = clients.get(sock)
                    cl.recv(4096)

            for sock in writable:
                pass

            for sock in exceptions:
                pass






if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
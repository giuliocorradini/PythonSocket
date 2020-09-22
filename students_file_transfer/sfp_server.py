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
import queue

__author__ = 'Giulio Corradini'

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


class ClientHandler(threading.Thread):
    CLIENT_NUMBER = 0

    def __init__(self):
        super().__init__(name="Client{}".format(ClientHandler.CLIENT_NUMBER))
        ClientHandler.CLIENT_NUMBER += 1

        self.buffer = bytearray()
        self.new_data_condition = threading.Condition()
        self.connection_closed = threading.Event()
        self.response_queue = queue.SimpleQueue()

    def run(self):
        while True:
            with self.new_data_condition:
                self.new_data_condition.wait()
                response = self.decodeProtocol()
                self.response_queue.put(response)


    def feedBuffer(self, data: bytes):
        with self.new_data_condition:
            self.buffer += data
            self.new_data_condition.notify()

    def getResponse(self) -> bytes:
        pass

    def decodeProtocol(self):
        '''
        Decodes a message from the buffer. The responder is stateful, every
        thread should istantiate its own.
        :param ingoing: socket ingoing buffer as bytearray
        :return: 0 is a full message has been processed
        1 if the incoming message is incomplete. The lower layer may call recv
        Remaining bytes to request to process current message
        '''
        ret = bytes(self.buffer)
        self.buffer.clear()
        return ret




def main(host, port):
    '''
    Front desk. Manages the registration of clients.
    :param host: host to bind the listening socket to
    :param port: port to listen to
    :return:
    '''

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as frontdesk_sock:
        frontdesk_sock.bind((host, port))
        frontdesk_sock.listen(5)
        frontdesk_sock.setblocking(False)

        active_socks = [frontdesk_sock]
        clients: Dict[socket.socket, ClientHandler] = {}

        while True:
            readable, writable, exceptions = select.select(active_socks, active_socks, active_socks, 10)
            for sock in readable:

                if sock is frontdesk_sock:
                    conn, addr = sock.accept()
                    conn.setblocking(False)
                    active_socks.append(conn)
                    cl = ClientHandler()
                    clients[conn] = cl
                    cl.start()
                    logging.info("New {} connected from {}".format(cl.name, addr))


                else:
                    cl = clients.get(sock)
                    if cl:
                        data = sock.recv(4096)
                        if not data:
                            logging.info("Client {} has closed the connection".format(cl.name))
                            sock.close()
                            cl.connection_closed.set()
                            cl.join()
                        else:
                            cl.feedBuffer(data)


            for sock in writable:
                cl = clients.get(sock)
                if cl:
                    if not cl.response_queue.empty():
                        sock.sendall(cl.response_queue.get())

            for sock in exceptions:
                pass

        logging.info("Closing")






if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9998, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
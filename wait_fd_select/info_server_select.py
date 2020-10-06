'''
info_server_select.py

TCP-based multi-client application protocol to provide users information
about running threads and connection sockets.
Protocol is described in naive_server.py

Model: non-blocking
Fashion: select
'''

__author__ = 'Giulio Corradini'

import sys
import argparse
import logging
import socket
from select import select
from typing import Set
import threading

quit_on_idle = False
closing = False

class ClientSession(socket.socket):
    session_count = 0

    def __init__(self, clientsocket: socket.socket):
        super().__init__(fileno=clientsocket.fileno())

        self.session_count = ClientSession.session_count + 1
        ClientSession.session_count += 1

        self.write_buffer = bytearray()
        self.read_buffer = bytearray()

        logging.info(f"{self.getpeername()} connected as client #{self.session_count}")

    def processCommand(self, command: str):
        global quit_on_idle
        if command == '0':
            return str(self.getpeername())
        elif command == '1':
            return str(self.getsockname())
        elif command == '2':
            return str(self.session_count)
        elif command == '3':
            return str(threading.active_count())
        elif command == '4':
            return ', '.join(t.name for t in threading.enumerate())
        elif command == 'q':
            quit_on_idle = True
            logging.debug("Client {} set quitting on idle".format(self.getpeername()))
            return "Quitting on idle"
        else:
            return "Not recognized."

    def processData(self):
        command = self.read_buffer[:1].decode()
        del self.read_buffer[:1]
        response = self.processCommand(command) + '\n'
        self.sendall(response.encode())

        return

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        data = super().recv(bufsize, flags)
        self.read_buffer += data
        return data

    def sendall(self, data: bytes, flags: int = ...) -> None:
        self.write_buffer += data

    def flushWriteBuffer(self) -> int:
        sent = super().send(self.write_buffer)
        del self.write_buffer[:sent]
        return sent

def main(host, port):
    global closing
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)

        active_clients = [s]
        socket_history = [] # Socket direct ref. needed
        closed_clients: Set[ClientSession] = set()

        logging.info("Non-blocking select server started")
        try:

            while active_clients:
                if quit_on_idle and not closing:
                    active_clients.remove(s)
                    closing = True

                readable, writable, errors = select(active_clients, active_clients, [])

                for r in readable:
                    if r is s:
                        conn, addr = r.accept()
                        socket_history.append(conn)
                        active_clients.append(ClientSession(conn))

                    else:
                        data = r.recv(1024)
                        if not data: closed_clients.add(r)
                        else:
                            while r.read_buffer:
                                r.processData() # Process all available data

                for w in writable:
                    if w.write_buffer:
                        sent = w.flushWriteBuffer()
                        if not sent: closed_clients.add(w)

                for cl in closed_clients:
                    cl.close()
                    active_clients.remove(cl)
                    logging.info(f"Client #{cl.session_count} disconnected")
                closed_clients.clear()

        except KeyboardInterrupt:
            logging.info("Shutting down")

    logging.info("Goodbye")

if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
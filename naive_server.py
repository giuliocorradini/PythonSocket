'''
naiveserver.py

Implementazione di un server TCP con protocollo applicativo custom,
utilizzando l'API socket della libreria standard Python
e con gestione multithreaded delle richieste.

The protocol is defined as follows:
command     return description                              example
0           Address of connected client socket as tuple     ('127.0.0.1', 62820)
1           Server own socket address                       ('127.0.0.1', 9999)
2           Handler current thread name                     Client 1
3           Number of alive threads                         3
4           Comma-separated list of alive threads' names    Client1, Client2, MainThread
q           Quit server when all clients disconnect         Quitting all threads

Client requests are ASCII encoded strings up to 3 bytes.
Response strings are ASCII encoded, without NL nor CR.
'''

__author__ = "Giulio Corradini"

import socket
import threading
import logging

quit_on_idle = threading.Event()
shutdown = threading.Event()

class ThreadedRequestHandler(threading.Thread):

    _count = 0

    def __init__(self, incoming_conn):
        super().__init__(name="Client {}".format(ThreadedRequestHandler._count))
        self.conn: socket.socket = incoming_conn
        self.conn.setblocking(False)

        self.buffer = bytearray()

        ThreadedRequestHandler._count += 1

    def protocolCommandHandler(self, command: str) -> str:
        if command == '0':
            return str(self.conn.getpeername())
        elif command == '1':
            return str(self.conn.getsockname())
        elif command == '2':
            return self.name
        elif command == '3':
            return str(threading.active_count())
        elif command == '4':
            return ', '.join(t.name for t in threading.enumerate())
        elif command == 'q':
            quit_on_idle.set()
            logging.info("Client {} set quitting on idle".format(self.conn.getpeername()))
            return "Quitting on idle"
        else:
            raise ValueError("Command not recognized.")

    def run(self) -> None:
        while True:
            try:
                data = self.conn.recv(1024)
                if not data: break
                self.buffer += data

                command = self.buffer[:1].decode("ascii")
                del self.buffer[:2]
                try:
                    response = self.protocolCommandHandler(command)
                except ValueError:
                    logging.error("Client {} sent an invalid command {}".format(self.conn.getpeername(), data))
                    response = "Invalid command"
                finally:
                    self.conn.sendall(bytes(response, 'ascii'))

            except BlockingIOError:
                if shutdown.is_set(): break

            except ConnectionResetError:
                #Client disconnects    client-/->server
                logging.info("Client {} disconnected".format(self.conn.getpeername()))
                break

        #Close connection from sock->server
        self.conn.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 9999))
        s.listen(5)
        s.setblocking(False)

        logging.info("Opened a socket")

        while not shutdown.is_set():
            try:
                conn, addr = s.accept()
                logging.info("Accepted connection request from {}".format(addr))
                t = ThreadedRequestHandler(conn)
                t.start()

            except BlockingIOError:
                if quit_on_idle.is_set(): break

            except KeyboardInterrupt:
                shutdown.set()

        logging.warning("Started shutdown procedure")
        for t in threading.enumerate():
            if t != threading.current_thread():
                t.join()

        logging.debug("Quit")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.DEBUG)
    main()
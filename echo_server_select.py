'''
Echo server using select system call

Select lets you monitor a set of file descriptors (streams, sockets and
other devices), hence we can use it for a multiplexing-IO approach.

Select is still a blocking function, but it returns as soon as one the
monitored sockets becomes available to read or write.

Another closely related I/O model is to use multithreading with blocking I/O.
That model very closely resembles the model described above, except that
instead of using select to block on multiple file descriptors, the program
uses multiple threads (one per file descriptor), and each thread is then
free to call blocking system calls like recv.

When does a socket become available to read or write?
A socket is marked as available when:
    [read-only]
    • it's a listening socket and a client wants to connect;
    • a read operation will not block either because there's actual
        data to read (recv will return >1) or the read-half of socket
        is closed (recv will return 0)
    [write-only]
    • available bytes in the buffer are > 0, thus send will not block
    • the write-half of connection is closed, send will return 0
    [both read&write]
    • a socket error is pending

Reference: UNIX Network Programming - Third Edition - Vol I Chapter 6
'''

__author__ = "Giulio Corradini"

import sys
import socket
import logging
import argparse
import select

from collections import defaultdict
from typing import Dict

def main(host, port):
    '''
    Front desk. Manages the registration of clients.
    WITHOUT using threads.
    :param host: host to bind the listening socket to
    :param port: port to listen on
    '''

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fds:
        fds.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # For debug purposes on UNIX
        fds.bind((host, port))
        fds.listen(5)

        active = [fds]
        buffers: Dict[socket.socket, bytearray] = defaultdict(bytearray)

        logging.info("Started server")

        while True:
            try:
                readable, writable, exceptions = select.select(active, active, [])
                for sock in readable:

                    if sock is fds:
                        conn, addr = sock.accept()
                        active.append(conn)
                        logging.info("A new client connected with address {}".format(addr))

                    else:
                        data = sock.recv(4096)
                        if not data:
                            active.remove(sock)
                            sock.close()
                            logging.warning("{} disconnected".format(sock.getpeername()))
                        else:
                            buffers[sock] += data

                for sock in writable:
                    response = buffers.get(sock)
                    if response:    # Available response [bytes] to send
                        sent = sock.send(response)
                        if sent == 0:   # Socket closed by other end
                            sock.close()
                            active.remove(sock)
                            logging.warning("{} disconnected".format(sock.getpeername()))
                        else:
                            del response[:sent] # Remove sent bytes from bytearray

            except KeyboardInterrupt:
                for sock in active:
                    if not sock is fds:
                        sock.close()
                break

    logging.info("Goodbye")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
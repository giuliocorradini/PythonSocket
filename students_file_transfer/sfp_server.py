'''
sfp_server.py

Students File Protocol server implementation.
Using blocking-IO model and threading.

Protocol is defined in README.md of this directory.
'''

import socket
import os
import glob
import logging
import argparse
import sys
import threading
import datetime as dt

__author__ = 'Giulio Corradini'


class SFPClientHandler(threading.Thread, socket.socket):
    CLIENT_NUMBER = 0

    def __init__(self, conn: socket.socket):
        threading.Thread.__init__(self, name="Client{}".format(SFPClientHandler.CLIENT_NUMBER))
        socket.socket.__init__(self, fileno=conn.fileno())
        SFPClientHandler.CLIENT_NUMBER += 1

        self.buffer = bytearray()
        self.conn = conn
        self.user: str = None
        self.working_directory: str = None

    def run(self):
        while True:

            if self.user == None:   #Read authentication string
                logging.debug("User requires auth".format(self.name))
                auth_str_end = self.readUntil(b'\n')
                self.user = self.consumeBuffer(auth_str_end).decode('utf-8').rstrip('\n')

                self.working_directory = dt.datetime.today().strftime("%Y%m%d") + self.user
                if not os.path.exists(self.working_directory):
                    os.mkdir(self.working_directory)

                logging.debug("{} logged in".format(self.user))


            command = self.consumeBuffer( self.readUntil(b'\n') )\
                        .decode('utf-8')\
                        .split(' ', 3)

            # Parse commands
            if command[0] == 'U':
                filesize, filename = command[1:]
                filesize = int(filesize)

                if os.path.exists(os.path.join(self.working_directory, filename)):
                    self.sendall(b'EXISTS')
                    continue
                else:
                    with open(os.path.join(self.working_directory, filename), 'bw') as fd:
                        recv_size = 0
                        while recv_size < filesize:
                            self.buffer = self.conn.recv(4096)
                            recv_size = len(self.buffer)

                        fd.write(self.buffer)
                    self.buffer.clear()


            elif command[0] == 'D':
                pass
            elif command[0] == 'L':
                pass
            elif command[0] == 'H':
                pass

            elif command[0] == 'Q':
                self.close()
                break


    #   Utility functions for socket buffer management
    def readUntil(self, char: bytes) -> int:
        '''
        Receives bytes from the socket until char is met.
        :param char: byte value to look for
        :return: char position in self.buffer
        '''
        str_end = -1
        while str_end == -1:
            self.buffer += self.conn.recv(4096)
            str_end = self.buffer.find(b'\n')

        return str_end

    def consumeBuffer(self, n=0, include_last=True) -> bytearray:
        '''
        Consume bytes from self.buffer and deletes from it
        :param n: Position of last byte to consume
        :param include_last: Include n-th byte in consumed slice
        :return: bytearray slice in range [0; n]
        '''
        if include_last:
            n += 1
        consumed = self.buffer[:n]
        del self.buffer[:n]
        return consumed

    def recvleast(self, n):
        received = 0
        while received < n:
            data = self.recv(4096)
            self.buffer += data
            received = len(data)

    def recv(self, *args, **kwargs) -> bytes:
        '''
        Reimplemented recv with auto-check and close
        '''
        data = super().recv(*args, **kwargs)
        if not data:
            self.close()
            logging.warning("{} disconnected".format(self.name))
        return data


def main(host, port):
    '''
    Front desk. Manages the registration of clients.
    :param host: host to bind the listening socket to
    :param port: port to listen on
    :return:
    '''


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fds:
        fds.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # For debug purposes on UNIX
        fds.bind((host, port))
        fds.listen(5)

        logging.info("Blocking-IO model + threading server started.")

        clients = []

        try:
            while True:
                conn, addr = fds.accept()
                logging.info("New client connected {}".format(conn.getpeername()))
                t = SFPClientHandler(conn)
                t.start()

                clients.append(t)

        except KeyboardInterrupt:
            for cl in clients:
                cl.close()  # Close socket, may fail some calls
                cl.join()   # Join thread

    logging.info("Closing")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
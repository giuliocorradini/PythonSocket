'''
sfp_server.py

Students File Protocol server implementation.
Using blocking-IO model and threading.

Protocol is defined in README.md of this directory.
'''

import socket
import socketserver
import os
import logging
import argparse
import sys
import datetime as dt

__author__ = 'Giulio Corradini'


class SFPClientHandler(socketserver.BaseRequestHandler, socket.socket):
    CLIENT_NUMBER = 0

    def __init__(self, request, client_address, server):
        socket.socket.__init__(self, fileno=request.fileno())
        SFPClientHandler.CLIENT_NUMBER += 1

        self.buffer = bytearray()
        self.user: str = None
        self.working_directory: str = None

        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self) -> None:
        try:
            while True:
                if self.user == None:   #Read authentication string
                    logging.debug("User requests auth")
                    auth_str_end = self.readUntil(b'\n')
                    self.user = self.consumeBuffer(auth_str_end).decode('utf-8').rstrip('\n')

                    self.working_directory = dt.datetime.today().strftime("%Y%m%d") + self.user
                    if not os.path.exists(self.working_directory):
                        os.mkdir(self.working_directory)

                    logging.debug("{} logged in".format(self.user))


                command = self.consumeBuffer( self.readUntil(b'\n') )\
                            .decode('utf-8')[:-1]\
                            .split(' ', 3)

                # Parse commands
                if command[0] == 'U':
                    filename, filesize = command[1:]
                    filesize = int(filesize)

                    path = os.path.join(self.working_directory, filename)

                    if os.path.exists(path):
                        self.sendall(b'EXISTS\n')
                        continue
                    else:
                        self.sendall(b'OK\n')
                        with open(path, 'bw') as fd:
                            self.recvLeast(filesize)
                            fd.write(self.consumeBuffer(filesize))

                        logging.info(f"{self.user} uploaded a file: {filename}")

                elif command[0] == 'D':
                    fname, date = command[1:]

                    found = None
                    for dirpath, _, filenames in os.walk(f"{date}{self.user}"):
                        if fname in filenames:
                            found = os.path.join(dirpath, fname)

                    if found:
                        filesize = os.stat(found).st_size
                        self.sendall(f"{filesize}\n".encode('utf-8'))
                        with open(found, 'rb') as fd:
                            self.sendall(fd.read())
                    else:
                        self.sendall(b'NOTFOUND\n')

                elif command[0] == 'L':
                    date = command[1]

                    filelist = None
                    for _, _, filenames in os.walk(f"{date}{self.user}"):
                        filelist = ", ".join(filenames) + "\n"
                        self.sendall(filelist.encode('utf-8'))
                        break

                    if not filelist: self.sendall(b'NOTFOUND\n')

                elif command[0] == 'H':
                    self.sendall('''Students File Protocol commands usage:
                    U - Upload a file
                    D - Download a file
                    L - List files in directory
                    H - Show this help message
                    Q - Disconnect from server, close client\n\n'''.encode('utf-8'))

                elif command[0] == 'Q':
                    self.sendall(b'GOODBYE\n')
                    logging.info("Client has notified disconnection")
                    break

                else:
                    self.sendall(b'INVALID\n')

        except socket.error:
            logging.info("Connection reset")

        logging.info("Finished")

    def recv(self, *args, **kwargs) -> bytes:
        '''
        Reimplemented recv with auto-check and close
        '''
        data = super().recv(*args, **kwargs)
        if not data:
            logging.warning("{} disconnected".format(self.user))
            raise socket.error()
        return data

    def recvLeast(self, n):
        received = 0
        while received < n:
            data = self.recv(4096)
            self.buffer += data
            received += len(data)

    #   Utility functions for socket buffer management
    def readUntil(self, char: bytes) -> int:
        '''
        Receives bytes from the socket until char is met.
        :param char: byte value to look for
        :return: char position in self.buffer
        '''
        str_end = -1
        while str_end == -1:
            self.buffer += self.recv(4096)
            str_end = self.buffer.find(char)

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



def main(host, port):
    '''
    Front desk. Manages the registration of clients.
    :param host: host to bind the listening socket to
    :param port: port to listen on
    '''

    logging.info(f"Starting server on port {port}")

    with socketserver.ThreadingTCPServer((host, port), SFPClientHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info("Exiting")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
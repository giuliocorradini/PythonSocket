import socket
import logging
import argparse
import sys
import os

class SFPClientHandler(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.buffer = bytearray()
        self.user: str = None

    def uploadFile(self, filename):
        pass

    def downloadFile(self, filename):
        pass

    def sendTextCommand(self, command: str) -> str:
        pass


    #   Utility functions for socket buffer management
    def recvUntil(self, char: bytes) -> int:
        '''
        Receives bytes from the socket until char is met.
        :param char: byte value to look for
        :return: char position in self.buffer
        '''
        str_end = -1
        while str_end == -1:
            self.buffer += self.recv(4096)
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
            raise socket.error()
        return data

def main(host, port):
    with SFPClientHandler(socket.AF_INET, socket.SOCK_STREAM) as s:
        buffer = bytearray()
        def feedBuffer(size: int):
            received = 0
            while received < size:
                data = s.recv(1024)
                if not data:
                    break
                else:
                    buffer += data


        try:
            s.connect((host, port))

            user = input("What's your name?")
            s.sendall(user.encode('utf-8')+b'\n')

            while True:
                command = input(">> ")
                if command[0] == 'U':
                    filename = input("Enter filename: ")
                    if os.path.exists(filename):
                        filesize = os.stat(filename).st_size

                message = "U {} {}\n".format(filesize, os.path.split(filename)[-1])
                s.sendall(message.encode('utf-8'))

                msg_size = s.recvUntil('\n')
                can_tx = s.consumeBuffer(msg_size)[:-1]
                if can_tx == 'OK':
                    #Start transmitting file
                    with open(filename, 'rb') as fd:
                        s.sendall(bytes(fd.read()))

        except socket.timeout as e:
            logging.error(e)

        except ConnectionAbortedError:
            logging.info("Server forced a disconnection")

        s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-host", metavar="host", type=str, default='localhost', required=False)
    parser.add_argument("-port", metavar="port", type=int, default=9999, required=False)

    args = parser.parse_args(sys.argv[1:])

    main(args.host, args.port)
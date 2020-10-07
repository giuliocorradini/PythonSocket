import socket
import logging
import argparse
import sys
import os
import datetime

__author__ = 'Giulio Corradini'

class SFPClientHandler(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.buffer = bytearray()
        self.user: str = None

    def uploadFile(self, filename, filesize):
        command = f"U {filename} {filesize}\n".encode('utf-8')
        self.sendall(command)

        can_tx = self.consumeBuffer(self.recvUntil(b'\n'))
        if can_tx == b'OK\n':
            with open(filename, 'rb') as fd:
                self.sendall(fd.read())
        elif can_tx == b'EXISTS\n':
            print("File exists")
        else:
            print("Server error")

    def downloadFile(self, filename, date):
        command = f"D {filename} {date}\n".encode('utf-8')
        self.sendall(command)

        response = self.consumeBuffer(self.recvUntil(b'\n'))
        if response == b'NOTFOUND\n':
            print("File not found on server")

        elif response == b'ERROR\n':
            print("Server error")

        else:
            filesize = int(response.decode('utf-8'))
            self.recvLeast(filesize)
            with open(filename, 'wb') as fd:
                fd.write(self.consumeBuffer(filesize))
            print(f"Received {filesize} bytes")

    def sendTextCommand(self, command: str, payload: str = None) -> str:
        command += f" {payload}\n"

        self.sendall(command.encode('utf-8'))
        if command[0] == 'H':
            response = self.consumeBuffer(self.recvUntil(b'\n\n'))
        else:
            response = self.consumeBuffer(self.recvUntil(b'\n'))
        return response.decode('utf-8')

    def auth(self, user: str) -> bool:
        self.sendall(user.encode('utf-8') + b'\n')
        auth_result = self.consumeBuffer(self.recvUntil(b'\n'))
        if auth_result == b'OK\n':
            return True
        else:
            return False

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

    def recvLeast(self, n):
        received = 0
        while received < n:
            data = self.recv(65536)
            self.buffer += data
            received += len(data)

    def recv(self, *args, **kwargs) -> bytes:
        '''
        Reimplemented recv with auto-check and close
        '''
        data = super().recv(*args, **kwargs)
        if not data:
            self.close()
            raise socket.error()
        return data

def main(host, port):
    with SFPClientHandler(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((host, port))

            user = input("What's your name?")
            if not s.auth(user):
                print("User authentication error")
                raise KeyboardInterrupt()

            while True:
                command = input(">> ")

                if command[0] == 'U':
                    filename = input("Enter filename: ")
                    if os.path.exists(filename):
                        filesize = os.stat(filename).st_size
                    else:
                        print("This file doesn't exist")
                        continue

                    s.uploadFile(filename, filesize)

                elif command[0] == 'D':
                    dirname = input("What day did you upload the file?(yyyymmdd) ")
                    if not dirname: dirname = datetime.datetime.now().strftime("%Y%m%d")
                    filename = input("Enter filename: ")
                    if os.path.exists(filename):
                        overwrite = input("File exists. Overwrite?[y/n] ")
                        if overwrite != 'y':
                            print("File download aborted")
                            continue

                    s.downloadFile(filename, dirname)

                elif command[0] == 'L':
                    dirname = input("What day do you want to search for?(yyyymmdd) ")
                    if not dirname: dirname = datetime.datetime.now().strftime("%Y%m%d")
                    print(s.sendTextCommand('L', dirname))

                elif command[0] == 'Q':
                    print(s.sendTextCommand('Q'))
                    break

                else:
                    print(s.sendTextCommand(command[0]))

        except KeyboardInterrupt:
            logging.info("Disconnecting")

        except ConnectionResetError:
            logging.info("Server forced a disconnection")

        logging.info("Closing connection")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", metavar="host", type=str, default='localhost', required=False)
    parser.add_argument("--port", metavar="port", type=int, default=9999, required=False)

    args = parser.parse_args(sys.argv[1:])

    main(args.host, args.port)
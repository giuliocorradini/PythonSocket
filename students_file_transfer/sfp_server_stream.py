'''
sfp_server.py

Students File Protocol server implementation.
Using blocking-IO model, threading and streams.

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


class SFPClientHandler(socketserver.StreamRequestHandler):
    CLIENT_NUMBER = 0

    def setup(self):
        super().setup()
        SFPClientHandler.CLIENT_NUMBER += 1

        self.user: str = None
        self.working_directory: str = None

    def handle(self) -> None:
        try:
            while True:
                if self.user == None:   #Read authentication string
                    logging.debug("User requests auth")

                    user_auth_str = self.rfile.readline()\
                                                .decode('utf-8')\
                                                .rstrip('\n')
                    sanitized = self.sanitizeInput(user_auth_str)   # Since a user might inject a malicious
                                                                    # path as its username (e.g. ../)

                    if not sanitized:
                        self.wfile.write(b'ERROR\n')
                        logging.warning("Sent an invalid sequence as login name. Forcing disconnection")
                        break
                    else:
                        self.wfile.write(b'OK\n')
                    self.user = sanitized

                    self.working_directory = dt.datetime.today().strftime("%Y%m%d") + self.user
                    if not os.path.exists(self.working_directory):
                        os.mkdir(self.working_directory)

                    logging.debug("{} logged in".format(self.user))


                command = self.rfile.readline()\
                            .decode('utf-8')\
                            .rstrip('\n')\
                            .split(' ', 3)

                # Parse commands
                if command[0] == 'U':
                    filename, filesize = command[1:]

                    try:
                        filesize = int(filesize)
                    except ValueError:
                        self.wfile.write(b'ERROR\n')
                        continue

                    filename = self.sanitizeInput(filename)

                    path = os.path.join(self.working_directory, filename)

                    if os.path.exists(path):
                        self.wfile.write(b'EXISTS\n')
                        continue
                    else:
                        self.wfile.write(b'OK\n')
                        with open(path, 'bw') as fd:
                            data = self.rfile.read(filesize)
                            fd.write(data)

                        logging.info(f"{self.user} uploaded a file: {filename}")

                elif command[0] == 'D':
                    fname, date = command[1:]
                    fname = self.sanitizeInput(fname)
                    if not self.sanitizeInput(date, type="date"):
                        self.wfile.write(b'ERROR\n')
                        continue

                    found = None
                    for dirpath, _, filenames in os.walk(f"{date}{self.user}"):
                        if fname in filenames:
                            found = os.path.join(dirpath, fname)

                    if found:
                        filesize = os.stat(found).st_size
                        self.wfile.write(f"{filesize}\n".encode('utf-8'))
                        with open(found, 'rb') as fd:
                            self.wfile.write(fd.read())
                    else:
                        self.wfile.write(b'NOTFOUND\n')

                elif command[0] == 'L':
                    date = command[1]
                    if not self.sanitizeInput(date, type="date"):
                        self.wfile.write(b'ERROR\n')
                        continue

                    filelist = None
                    for _, _, filenames in os.walk(f"{date}{self.user}"):
                        filelist = ", ".join(filenames) + "\n"
                        self.wfile.write(filelist.encode('utf-8'))
                        break

                    if not filelist: self.wfile.write(b'NOTFOUND\n')

                elif command[0] == 'H':
                    self.wfile.write('''Students File Protocol commands usage:
                    U - Upload a file
                    D - Download a file
                    L - List files in directory
                    H - Show this help message
                    Q - Disconnect from server, close client\n\n'''.encode('utf-8'))

                elif command[0] == 'Q':
                    self.wfile.write(b'GOODBYE\n')
                    logging.info("Client has notified disconnection")
                    break

                else:
                    self.wfile.write(b'INVALID\n')

        except socket.error:
            logging.info("Connection reset")

        logging.info("Finished")

    def sanitizeInput(self, user_input: str, type = "str"):
        '''
        Sanitizes user input for path and dates.
        :param input: string to santize.
        :param type: "str" or "date", defines the sanity check method.
        :return: input without paths for str.
            True/False if date is valid.
        '''
        if type == "str":
            head, tail = os.path.split(user_input)
            return tail.strip().strip('.')  # Remove leading/trailing spaces and dots
        elif type == "date":
            try:
                dt.datetime.strptime(user_input, "%Y%m%d")
                return True
            except ValueError:
                return False


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
'''
sockserver_mod.py

TCP server using sockets and Python socketserver std module.

Protocol: depicted in naive_server.py
'''

__author__ = "Giulio Corradini"

import logging
import socket
import socketserver
import threading
import argparse
import sys

quitting_on_idle = threading.Event()

class CustomProtocolRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data = self.request.recv(2)
            if not data: break
            command = data.decode('ascii')
            try:
                response = self.commandDecoder(command[0])
            except ValueError as e:
                logging.error("Client {} sent unknown command: {}".format(self.client_address, data))
                response = str(e)
            finally:
                self.request.sendall(response.encode('ascii'))


    def commandDecoder(self, command: str):
        if command == '0':
            return str(self.client_address)
        elif command == '1':
            return str(self.server)
        elif command == '2':
            return threading.current_thread().name
        elif command == '3':
            return str(threading.active_count())
        elif command == '4':
            return ', '.join(t.name for t in threading.enumerate())
        elif command == 'q':
            quitting_on_idle.set()
            logging.info("Client {} asked to shutdown".format(self.client_address))
            return "Quitting on idle"
        else:
            raise ValueError("Command not recognized.")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main(host, port):
    with ThreadedTCPServer((host, port), CustomProtocolRequestHandler) as server:

        def checkForShutdown(): #closure
            while True:
                if quitting_on_idle.is_set():
                    server.shutdown()
                    break
        t = threading.Thread(target=checkForShutdown, daemon=True, name="Shutdown_Check")
        t.start()
        logging.info("Started a threaded TCP server on {}:{}".format(host, port))
        server.serve_forever()

if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    main(args.address, args.port)
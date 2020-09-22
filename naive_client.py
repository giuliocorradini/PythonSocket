import socket
import logging
import argparse
import sys

def main(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))

            while True:
                command = input(">> ")
                s.sendall(command.encode('ascii'))

                response = s.recv(1024)
                if not response: break
                print(response.decode('ascii'))

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
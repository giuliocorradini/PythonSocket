'''
asyncio_dummies.py

AsyncIO Dummies Protocol

Non-blocking I/O model using AsyncIO module and asyncsockets
'''

__author__ = 'Giulio Corradini'

import asyncio
import logging
import sys
import argparse

async def handle_client(reader, writer):
    while True:
        command =
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

async def main(host, port):
    server = await asyncio.start_server()

if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    asyncio.run(main(args.address, args.port))
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
import threading

client_counter = 0

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global client_counter
    this_client = client_counter
    client_counter += 1

    logging.info(f"Client {client_counter} connected")

    while True:
        try:
            command = await reader.readexactly(1)
        except asyncio.IncompleteReadError:
            logging.info(f"Client {this_client} closed the connection")
            break

        if command == b'0':
            response = str(writer.get_extra_info("peername"))
        elif command == b'1':
            response = str(writer.get_extra_info("sockname"))
        elif command == b'2':
            response = str(this_client)
        elif command == b'3':
            response = str(threading.active_count())
        elif command == b'4':
            response = ', '.join(t.name for t in threading.enumerate())
        elif command == b'q':
            response = "Goodbye"
        else:
            response = "Not recognized."
            logging.warning(f"Client {this_client} sent an unrecognized command {command}")

        writer.write(f"{response}\n".encode())
        await writer.drain()


async def main(host, port):
    server = await asyncio.start_server(handle_client, host, port)

    logging.info(f"Started server on {server.sockets[0].getsockname()} {port}")

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    asyncio.run(main(args.address, args.port))
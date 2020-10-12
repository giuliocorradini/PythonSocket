'''
dummies_client.py

Socket for dummies client using AsyncIO
'''

__author__ = 'Giulio Corradini'

import sys
import argparse
import asyncio
import logging

async def main(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    closed = False
    while not closed:
        command = input(">> ")
        writer.write(command.encode())
        await writer.drain()

        for _ in command:
            response = await reader.readline()
            print(response.decode(), end='')

        if 'q' in command:
            closed = True

    logging.debug("Closing connection")
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    asyncio.run(main(args.address, args.port))
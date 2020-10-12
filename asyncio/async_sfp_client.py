'''
async_sfp_client.py

Students File Protocol Client
using AsyncIO
'''

__author__ = 'Giulio Corradini'

import argparse
import sys
import os
import datetime
import asyncio

class SFPClient:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def uploadFile(self, filename, filesize):
        command = f"U {filename} {filesize}\n".encode('utf-8')
        self.writer.write(command)
        await self.writer.drain()

        can_tx = await self.reader.readline()
        if can_tx == b'OK\n':
            with open(filename, 'rb') as fd:
                self.writer.write(fd.read())
                await self.writer.drain()
        elif can_tx == b'EXISTS\n':
            print("File exists")
        else:
            print("Server error")

    async def downloadFile(self, filename, date):
        command = f"D {filename} {date}\n".encode('utf-8')
        self.writer.write(command)
        await self.writer.drain()

        response = await self.reader.readline()
        if response == b'NOTFOUND\n':
            print("File not found on server")

        elif response == b'ERROR\n':
            print("Server error")

        else:
            filesize = int(response.decode('utf-8'))

            with open(filename, 'wb') as fd:
                fd.write(await self.reader.readexactly(filesize))
            print(f"Received {filesize} bytes")

    async def sendTextCommand(self, command: str, payload: str = None) -> str:
        command += f" {payload}\n"

        self.writer.write(command.encode('utf-8'))
        await self.writer.drain()
        if command[0] == 'H':
            response = await self.reader.readuntil(b'\n\n')
        else:
            response = await self.reader.readline()
        return response.decode('utf-8')

    async def auth(self, user: str) -> bool:
        self.writer.write(user.encode('utf-8') + b'\n')
        await self.writer.drain()

        auth_result = await self.reader.readline()
        if auth_result == b'OK\n':
            return True
        else:
            return False

async def main(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    client = SFPClient(reader, writer)

    logged = True
    user = input("What's your name?")
    if not await client.auth(user):
        print("User authentication error")
        logged = False

    while logged:
        command = input(">> ")

        if command[0] == 'U':
            filename = input("Enter filename: ")
            if os.path.exists(filename):
                filesize = os.stat(filename).st_size
            else:
                print("This file doesn't exist")
                continue

            await client.uploadFile(filename, filesize)

        elif command[0] == 'D':
            dirname = input("What day did you upload the file?(yyyymmdd) ")
            if not dirname: dirname = datetime.datetime.now().strftime("%Y%m%d")
            filename = input("Enter filename: ")
            if os.path.exists(filename):
                overwrite = input("File exists. Overwrite?[y/n] ")
                if overwrite != 'y':
                    print("File download aborted")
                    continue

            await client.downloadFile(filename, dirname)

        elif command[0] == 'L':
            dirname = input("What day do you want to search for?(yyyymmdd) ")
            if not dirname: dirname = datetime.datetime.now().strftime("%Y%m%d")
            print(await client.sendTextCommand('L', dirname))

        elif command[0] == 'Q':
            print(await client.sendTextCommand('Q'))
            logged = False

        else:
            print(await client.sendTextCommand(command[0]))

    print("Closing connection")

    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", metavar="host", type=str, default='localhost', required=False)
    parser.add_argument("--port", metavar="port", type=int, default=9999, required=False)

    args = parser.parse_args(sys.argv[1:])

    asyncio.run(main(args.host, args.port))
'''
sfp_server.py

Students File Protocol server implementation.
Using non-blocking IO model and asyncio.

Protocol is defined in README.md of this /students_file_transfer.
'''

import os
import logging
import argparse
import sys
import datetime as dt
import asyncio

__author__ = 'Giulio Corradini'

def sanitizeInput(user_input: str, type = "str"):
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


client_counter = 0

async def async_sfp_client_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global client_counter
    this_client = 0
    client_counter += 1

    logging.info(f"Client {client_counter} connected")
    user_auth_str = await reader.readline()
    user = sanitizeInput(user_auth_str.decode().rstrip('\n'))

    if not user:
        writer.write(b'ERROR\n')
        await writer.drain()
        logging.warning("Sent an invalid sequence as login name. Forcing disconnection")
        return

    else:
        writer.write(b'OK\n')
        await writer.drain()

        working_directory = dt.datetime.today().strftime("%Y%m%d") + user
        if not os.path.exists(working_directory):
            os.mkdir(working_directory)

        logging.debug("{} logged in".format(user))

    while True:

        raw_cmd = await reader.readline()
        command = raw_cmd.decode('utf-8').rstrip('\n').split(' ', 3)

        # Parse commands
        if command[0] == 'U':
            filename, filesize = command[1:]

            try:
                filesize = int(filesize)
            except ValueError:
                writer.write(b'ERROR\n')
                await writer.drain()

            filename = sanitizeInput(filename)

            path = os.path.join(working_directory, filename)

            if os.path.exists(path):
                writer.write(b'EXISTS\n')
                await writer.drain()
                continue
            else:
                writer.write(b'OK\n')
                await writer.drain()
                with open(path, 'bw') as fd:
                    fd.write(await reader.readexactly(filesize))

                logging.info(f"{user} uploaded a file: {filename}")

        elif command[0] == 'D':
            fname, date = command[1:]
            fname = sanitizeInput(fname)
            if not sanitizeInput(date, type="date"):
                writer.write(b'ERROR\n')
                await writer.drain()
                continue

            found = None
            for dirpath, _, filenames in os.walk(f"{date}{user}"):
                if fname in filenames:
                    found = os.path.join(dirpath, fname)

            if found:
                filesize = os.stat(found).st_size
                writer.write(f"{filesize}\n".encode('utf-8'))
                with open(found, 'rb') as fd:
                    writer.write(fd.read())
            else:
                writer.write(b'NOTFOUND\n')

            await writer.drain()

        elif command[0] == 'L':
            date = command[1]
            if not sanitizeInput(date, type="date"):
                writer.write(b'ERROR\n')
                await writer.drain()
                continue

            filelist = None
            for _, _, filenames in os.walk(f"{date}{user}"):
                filelist = ", ".join(filenames) + "\n"
                writer.write(filelist.encode('utf-8'))
                break

            if not filelist: writer.write(b'NOTFOUND\n')

            await writer.drain()

        elif command[0] == 'H':
            writer.write('''Students File Protocol commands usage:
            U - Upload a file
            D - Download a file
            L - List files in directory
            H - Show this help message
            Q - Disconnect from server, close client\n\n'''.encode('utf-8'))
            await writer.drain()

        elif command[0] == 'Q':
            writer.write(b'GOODBYE\n')
            await writer.drain()
            logging.info(f"{user} disconnected")
            break

        else:
            writer.write(b'INVALID\n')
            await writer.drain()



async def main(host, port):
    '''
    Front desk. Manages the registration of clients.
    :param host: host to bind the listening socket to
    :param port: port to listen on
    '''

    server = await asyncio.start_server(async_sfp_client_handler, host, port)

    logging.info(f"Starting server on {host} {port}")

    async with server:
        try:
            await server.serve_forever()
        except KeyboardInterrupt:
            logging.info("Exiting")


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s\t%(levelname)s\t%(threadName)s\t%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", "-a", default='', required=False, metavar="address")
    parser.add_argument("--port", "-p", type=int, default=9999, required=False, metavar="port")

    args = parser.parse_args(sys.argv[1:])
    asyncio.run(main(args.address, args.port))
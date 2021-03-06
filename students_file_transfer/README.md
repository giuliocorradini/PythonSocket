# Students File Protocol
## Specification

Written by Giulio Corradini

ITIS "Enrico Fermi" Modena

"Students File Protocol" is a custom defined protocol that
aims to transfer file in a client-server fashion between
students' PCs and a central server.

The session is carried by a TCP connection.

This protocol is usually implemented using **utf-8** encoding
although ASCII and other encodings may be implemented as well.
Server and client are constrained to agree on it.

### Session flow

1. The client connects to a server

2. The server requires authentication: a pair of name/surname.
It then creates a directory with the current day
and the student's name using the following format:
`yyyymmdd_surname_name`.
If user inputs an invalid name, an error message is returned
(`ERROR\n`) otherwise `OK\n` is returned and the client might
continue with its operations.

3. The server listens for commands from the client
and responds appropriately.

#### Uploading a file

a.  The client issues an `upload` command (see `U` in the commands table),
with the appropriate metadata.

b.  If the file doesn't exists the server responds with `OK\n`, `EXISTS\n` otherwise
and waits for a new command.

c.  The client starts transmitting the file as a RAW byte stream.

#### Downloading a file

a.  The client issues a `download` command (`D` verb) with requested filename and date.

b.  If the file doesn't exist the server responds with `NOTFOUND\n` and waits for a new command.
Otherwise, if the file's found the server transmits its size as a string, using this format:
`file_size\n`

c.  The server sends the file as a RAW byte stream of lenght *file_size*.

#### Text commands

4.  Server responds to text-only commands with a `\n\n` terminated string with the response.

5. Either client or server close the connection from their side.
    *NB. The client should issue a `Q` command first to gracefully disconnect.*

### Command structure

Each command is made up of a verb and an optional payload.
Given the stateful nature of the protocol, each response is
related to a sent command.

Every message is separated from one another using a UNIX
new line character `\n` or utf-8/ASCII `0x0a` `LF`.

**Client commands list**

| Verb | Description   | Payload                     | Response                                                                            |
|------|---------------|-----------------------------|-------------------------------------------------------------------------------------|
| U    | Upload file   | File name *space* File size | `OK` if file doesn't exists<br>`EXISTS` if file exists                              |
| D    | Download file | File name *space* Dirname   | `NOTFOUND` if file doesn't exists<br>`File size` if file exists                     |
| L    | List files    | Directory name to list      | Comma-separated list of file in student's disk space                                |
| H    | Show help     |                             | Help information about commands<br><br>Double `LF` terminated                       |
| Q    | Exit          |                             | GOODBYE *then close the TCP connection and quits*                                   |

If a server-related error occurs during any process, a message will be sent to
the client: `ERROR`. The client may clean its outgoing buffer, any data will
be treated as a new command by the server.
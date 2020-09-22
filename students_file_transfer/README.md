# Students File Protocol
## Specification

Written by Giulio Corradini

ITIS "Enrico Fermi" Modena

"Students File Protocol" is a custom defined protocol that
aims to transfer file in a client-server fashion between
students' PCs and a central server.

The session is carried by a TCP connection.

This protocol is usually implemented using **utf-8** encoding
although ASCII or other encodings may be implemented as well.

### Session flow

1. The client connects to a server

2. The server requires authentication: a pair of name/surname.
It then creates a directory with the current day
and the student's name using the following format:
`yyyymmdd_surname_name`.

3. The server listens for commands from the client
and responds appropriately.

4. Either client or server close the connection
from their side.

### Command structure

Each command is made up of a verb and an optional payload.
Given the stateful nature of the protocol, each response is
related to a sent command.

Every message is separated from one another using a UNIX
new line character `LF` or utf-8 `0x0a`.

| Verb | Description   | Payload                                                                                                                                | Response                                                                                       |
|------|---------------|----------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| U    | Upload file   | File size [8 byte]<br><br>UTF-8 encoded file name [max. 256 byte] (LF terminated)<br><br>RAW file as byte stream of length "file size" | Upload metrics string every second,<br>formatted as:<br><br>upload_progress%,speed_in_mbps`LF` |
| D    | Download file | UTF-8 encoded file name [max. 256 byte] (LF terminated)                                                                                | Code:<br>0 -> Successful upload<br>1 -> Existing file<br>2 -> Error                            |
| L    | List files    |                                                                                                                                        | Comma-separated list of file in student's disk space                                           |
| H    | Show help     |                                                                                                                                        | Help information about commands<br><br>Double `LF` terminated                                  |
| Q    | Exit          |                                                                                                                                        | *Close the TCP connection and quits*                                                           |

# PythonSocket

> Examples of TCP sockets using Python and different I/O models

## Usage

Every script can be launched with up to 2 parameters: `host` and `port`.
You may provide them to either connect to a remote machine or to change
port.

Default values for server scripts are host:`''`, port:`9999`.

Default values for client scripts are host:`localhost`, port:`9999`.

## Echo

The simplest TCP server is the *echo* service, every byte received
by a client is sent back to it (thus echoing its requests).

This simplicity makes the echo server suitable as an *Hello, world!* for
sockets.

An example is provided using the select system call.
> wait_fd_select/echo_server_select.py

## Sockets for dummies

As the name suggests, this is a simple implementation of a Layer 4 protocol
(application) and provides a kickstart for socket programming, that you might
further extend.

Different examples are provided using different I/O models:
- blocking I/O with *threading* in `naive_server.py`
- blocking I/O with *socketserver* in `sockserver_mod.py` 

## Students File Protocol (form. test result uploader)

This is a simple file transfer program that provides a quick way to move files
across the network, and provides a basic and raw authentication mechanism.

Both server and client are provided in `students_file_trasnfer` directory.

## Wait file descriptors with SELECT

A non-blocking I/O model using POSIX syscall select is a portable way of
programming networked applications.
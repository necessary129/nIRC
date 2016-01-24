#  Copyright (C) 2016 Muhammed Shamil K
#
#This file is part of nIRC.
#
#nIRC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nIRC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with nIRC.  If not, see <http://www.gnu.org/licenses/>.

from .numerics import numerics as numert
import re

# Copyright (C) oyoyo Python IRC developers
def parse_raw_irc_command(element):
    """
    This function parses a raw irc command and returns a tuple
    of (prefix, command, args).
    The following is a psuedo BNF of the input text:

    <message>  ::= [':' <prefix> <SPACE> ] <command> <params> <crlf>
    <prefix>   ::= <servername> | <nick> [ '!' <user> ] [ '@' <host> ]
    <command>  ::= <letter> { <letter> } | <number> <number> <number>
    <SPACE>    ::= ' ' { ' ' }
    <params>   ::= <SPACE> [ ':' <trailing> | <middle> <params> ]

    <middle>   ::= <Any *non-empty* sequence of octets not including SPACE
                   or NUL or CR or LF, the first of which may not be ':'>
    <trailing> ::= <Any, possibly *empty*, sequence of octets not including
                     NUL or CR or LF>

    <crlf>     ::= CR LF
    """
    parts = element.strip().split(" ")
    if parts[0].startswith(':'):
        prefix = parts[0][1:]
        command = parts[1]
        args = parts[2:]
    else:
        prefix = None
        command = parts[0]
        args = parts[1:]

    if command.isdigit():
        try:
            command = numert[command]
        except KeyError:
            pass
    command = command.lower()

    if args[0].startswith(':'):
        args = [" ".join(args)[1:]]
    else:
        for idx, arg in enumerate(args):
            if arg.startswith(':'):
                args = args[:idx] + [" ".join(args[idx:])[1:]]
                break
    result = re.search('\x01(.+)\x01',element)
    if result:
        if command == 'privmsg':
            command = 'ctcp'
        elif command == 'notice':
            command = 'ctcpreply'
        args[-1] = result.group(1)
    return (prefix, command, args)
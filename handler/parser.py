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


# Copyright (C) oyoyo Python IRC developers
def parse_nick(name):
    """ parse a nickname and return a tuple of (nick, mode, user, host)

    <nick> [ '!' [<mode> = ] <user> ] [ '@' <host> ]
    """

    try:
        nick, rest = name.split('!')
    except ValueError:
        return (name, None, None, None)
    try:
        user, host = rest.split('@')
    except ValueError:
        return (nick, rest, None)

    return (nick, user, host)
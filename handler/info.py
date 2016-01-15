#  Copyright (C) 2016 Muhammed Shamil K

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, download it from here: https://noteness.cf/GPL.txt
#  PDF: https://noteness.cf/GPL.pdf

from collections import defaultdict

from .parser import parse_nick
import fnmatch

class nDict(defaultdict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'{0}' object has no attribute '{1}'".format(self.__class__.__name__,key))
    def __setattr__(self, attr, value):
        self[attr] = value

class Dct(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dct' object has no attribute '%s'" % key)

    def __setattr__(self, attr, value):
        self[attr] = value

class ChannelUser:
    def __init__(self, nick, operator=False, voiced=False, quieted=False, 
        banned=False, account=None, raw=None, away=False):
        self.nick = nick
        self.operator = operator
        self.voiced = voiced
        self.quieted = quieted
        self.banned = banned
        self.account = account
        self.away = away

    def __eq__(self, another):
        return self.nick == another

    def __repr__(self):
        return "{self.__class__.__name__}(Op={self.operator},Voiced={self.voiced},Banned={self.banned},Quieted={self.quieted},Account={self.account},Away={self.away})".format(self=self)


class Nick:
    def __init__(self, raw):
        nick, ident, host = parse_nick(raw)
        self.name = nick
        self.ident = ident
        self.host = host

    @property
    def raw(self):
        return "{self.name}!{self.ident}@{self.host}".format(self=self)

    def match(self, wild):
        return fnmatch.fnmatch(self.raw, wild)

    def __eq__(self, another):
        if isinstance(another, ChannelUser):
            return self.__eq__(another.nick)
        if isinstance(another, Nick):
             return self.name == another.name and self.ident == another.ident and self.host == another.host
        if '!' not in another:
            if '.' in another or '/' in another:
                if not '@' in another:
                    raise TypeError("No Ident found")
                return (self.ident+self.host) == another
            return self.name == another
        return self.raw == another

    def __repr__(self):
        return "{self.__class__.__name__}(Nick='{self.name}',Ident='{self.ident}',Host='{self.host}')".format(self=self)


class Channel:
    def __init__(self, name, key=None, **kwargs):
        self.name = name
        self.key = key
        self.users = Dct()

    def __repr__(self):
        return "{self.__class__.__name__}({self.name})".format(self=self)

class States:
    def __init__(self, client, nick=None):
        self.nick = nick
        self.client = client

    def __setattr__(self, attr, value):
        if attr == 'nick' and 'nick' in self.__dict__:
            if value != self.__dict__['nick']:
                self.client.handler.nick_change()

        self.__dict__[attr] = value

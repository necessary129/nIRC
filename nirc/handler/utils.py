#  Copyright (C) 2016 Muhammed Shamil K

#This file is part of nIRC.

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

from . import info

class hook:
    def __init__(self, func, hookid=-1):
        self.func = func
        self.id = hookid

class cmd:
    def __init__(self, handler, cmd, func, owner_only=False,admin_only=False, pm=True):
        self.name = cmd
        self.admin_only = admin_only
        self.pm = pm
        self.owner_only = owner_only
        self.handler = handler
        self.func = func

    def call(self, cli, nick, channel, msg):
        isch = isinstance(channel, info.Channel)
        if self.owner_only:
            if not self.handler.is_owner(nick):
                nick.notice("You are not an owner.")
                return
        if self.admin_only:
            if (not self.handler.is_admin(nick)):
                nick.notice("You are not an admin.")
                return
        if (not self.pm) and not isch:
            nick.notice("PMing this command is not allowed.")
            return

        cli.admin_logger(" ".join((nick.raw if isinstance(nick, info.Nick) else nick.nick.raw, channel.name, self.name, msg)))
        return self.func(cli, nick, channel, isch, msg)


FUNCS = {}

def add_f(name):
    def f(func):
        FUNCS[name] = func
        return func
    return f

def ret_f():
    for f,y in FUNCS.items():
        yield f,y

@add_f('add_handler')
def a_h(self, event, hookid=-1):
    def reg(func):
        self.handler.add_handler(event, func, hookid)
        return func
    return reg


@add_f('cmd')
def a_c(self, cmd, owner_only=False,admin_only=False, pm=True):
    def reg(func):
        self.handler.add_cmd(cmd, func, owner_only=owner_only,admin_only=admin_only, pm=pm)
        return func
    return reg

@add_f('del_handler')
def d_h(self, *args, **kwargs):
    return self.handler.del_handler(*args, **kwargs)


@add_f('nick')
@property
def nick(self):
    return self._opts.nick

@add_f('ident')
@property
def ident(self):
    return self._opts.ident

@add_f('host')
@property
def host(self):
    return self._opts.host

@add_f('channels')
@property
def host(self):
    return self.handler.channels
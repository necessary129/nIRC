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

import sys
from collections import defaultdict
from . import utils, info
import traceback
import re
import fnmatch

class Handler:
    def __init__(self, client):
        self.client = client
        for f,y in utils.ret_f():
            self.client.add_attr(f,y)
        self.hooks = defaultdict(list)
        self.orighooks = defaultdict(list)
        self.channels = info.Dct()
        self.cmds = defaultdict(list)
        self.quiets = defaultdict(set)
        self.handlers_do()

    def handlers_do(self):
        self.add_handler('privmsg',self.on_privmsg_cmd)
        self.add_handler('join', self.on_join)
        self.add_handler('ping', self.on_ping)
        self.add_handler('whospcrpl',self.on_whox)
        self.add_handler('quietlist',self.on_quietlist)
        self.add_handler('banlist',self.on_banlist)
        self.add_handler('pong', self.on_pong)  
        self.add_handler('part',self.on_part)
        self.add_handler('quit',self.on_quit)   
        self.add_handler('mode',self.on_mode)  

    def add_handler(self, event, func, hookid=-1):
        hook = utils.hook(func, hookid=hookid)
        self.hooks[event.lower()].append(hook)
        self.orighooks[event.lower()].append(hook)

    def del_handler(self, hookid):
        for each in list(self.hooks):
            for inner in list(self.hooks[each]):
                if inner.id == hookid:
                    self.hooks[each].remove(inner)
            if not self.hooks[each]:
                del self.hooks[each]

    def add_cmd(self, cmd, func, owner_only=False,admin_only=False, pm=True):
        cmds = utils.cmd(self, cmd, func, owner_only=owner_only,admin_only=admin_only, pm=pm)
        self.cmds[cmd.lower()].append(cmds)

    def recieve_raw(self, prefix, cmd, *args):
        for func in self.hooks.get(cmd, []):
            try:
                func.func(self.client, prefix, *args)
            except Exception:
                sys.stderr.write(traceback.format_exc())

    def connected(self):
        self.client.register()

    def is_admin(self, host):
        if isinstance(host, info.Nick):
            host = host.host
        if isinstance(host, info.ChannelUser):
            acc = host.account
            h = host.nick.host
            for a in (self.client.admin_accounts + self.client.owner_accounts):
                if fnmatch.fnmatch(acc, a):
                    return True
            for a in (self.client.admin_hosts + self.client.owner_hosts):
                if fnmatch.fnmatch(h, a):
                    return True
            return False
        if '.' in host or '/' in host or ':' in host:
            l = (self.client.admin_hosts + self.client.owner_hosts)
        else:
            l = (self.client.admin_accounts + self.client.owner_accounts)

        for u in l:
            if fnmatch.fnmatch(host, u):
                return True
        return False

    def is_owner(self, host):
        if isinstance(host, info.Nick):
            host = host.host
        if isinstance(host, info.ChannelUser):
            acc = host.account
            h = host.nick.host
            for a in self.client.owner_accounts:
                if fnmatch.fnmatch(acc, a):
                    return True
            for a in self.client.owner_hosts:
                if fnmatch.fnmatch(h, a):
                    return True
            return False
        if '.' in host or '/' in host or ':' in host:
            l = self.client.owner_hosts
        else:
            l = self.client.owner_accounts

        for u in l:
            if fnmatch.fnmatch(host, u):
                return True
        return False

    ### Handlers ###
    def on_disconnect(self):
        self.hooks.update(self.orighooks)

    def on_join(self, cli, nick, channel):
        nicka = info.Nick(self.client, nick)
        if nicka.name == cli._opts.nick:
            cli.whox(channel)
            cli.banlist(channel)
            cli.quietlist(channel)
        else:
            self.channels[channel].users[nick] = info.ChannelUser(self.client, self.channels[channel], nick) 
            cli.whox(nicka.name)
            self.client.ping(':NEWUSER {0} {1}'.format(channel, nicka.name))

    def on_whox(self, cli, prefix, snick, numeric, channel, ident, 
        host, nick, status, account, gecos):
        self.client._opts.nick = snick
        if numeric != '254':
            return
        if channel not in self.channels:
            self.channels[channel] = info.Channel(self.client, channel)
        opped = '@' in status
        voiced = '+' in status
        away = 'G' in status
        acc = account if account != '0' else None
        raw = '{0}!{1}@{2}'.format(nick, ident, host)
        n = info.Nick(self.client, raw)
        self.channels[channel].users[nick] = info.ChannelUser(self.client, self.channels[channel], nick=n,
            operator=opped,account=acc,voiced=voiced,away=away)
        for channela in self.channels.values():
            if nick in channela.users:
                channela.users[nick] = info.ChannelUser(self.client, self.channels[channel], nick=n,
            operator=opped,account=acc,voiced=voiced,away=away)

    def on_ping(self, cli, _, text):
        cli.pong(text)

    def on_banlist(self, cli, prefix, snick, channel, ban, setter, time):
        for user in self.channels[channel].users.values():
            if user.nick.match(ban):
                user.banned = True

    def on_quietlist(self, cli, prefix, snick, channel, mode, ban, setter, time):
        self.quiets[channel].add(ban)
        for user in self.channels[channel].users.values():
            if user.nick.match(ban):
                user.quieted = True

    def on_mode(self, cli, prefix, channel, modes, *nicks):
        d = False
        n = 0
        for char in modes:
            if char == '+':
                d = True
                continue
            elif char == '-':
                d = False
                continue
            if char == 'o':
                self.channels[channel].users[nicks[n]].operator = d
            if char == 'b':
                for user in self.channels[channel].users.values():
                    if user.nick.match(nicks[n]):
                        user.banned = d
            if char == 'q':
                for user in self.channels[channel].users.values():
                    if user.nick.match(nicks[n]):
                        user.quieted = d
                if d:
                    self.quiets[channel].add(nicks[n])
                else:
                    self.quiets[channel].discard(nicks[n])
            if char == 'v':
                self.channels[channel].users[nicks[n]].voiced = d
            if char in info.ModeI.ArgModes:
                n += 1

    def on_nick(self, cli, prefix, nick):
        onick = prefix.split('!')[0]
        if onick == self.client.gnick:
            self.client._opts.nick = nick
        for channel in self.channels:
            if nick in channel.users.keys():
                channel.users[nick] = channel.users[onick]
                del channel.users[onick]
                channel.users[nick].nick.name = nick

    def on_pong(self, cli, _, _1, text):
        if not text.startswith("NEWUSER"):
            return
        text = text.split(' ')
        text.pop(0)
        channel = text[0]
        nick = text[1]
        for quiet in self.quiets[channel]:
            if self.channels[channel].users[nick].nick.match(quiet):
                self.channels[channel].users[nick].quieted = True

    def nick_change(self, *args, **kwargs):
        pass

    def on_part(self, cli, prefix, channel, msg=None):
        self.channels[channel].users.pop(prefix.split('!')[0], None)

    def on_quit(self, cli, prefix, msg=None):
        u = prefix.split('!')[0]
        for channel in self.channels.values():
            if u in channel.users:
                channel.users.pop(u)

    def on_privmsg_cmd(self, cli, prefix, channel, text):
        if channel.startswith('#'):
            channelo = self.channels.get(channel, None)
            if not channelo:
                return

            if not text.startswith(self.client.cmd_prefix):
                return
            cmd = text.split(' ', 1)[0][1:]
            try:
                t = text.split(' ', 1)[1].strip()
            except IndexError:
                t = ''
            n = prefix.split('!')[0]
            n = channelo.users.get(n, None)
            if not n:
                n = info.Nick(self.client, prefix)
            for cmds in self.cmds.get(cmd, []):
                cmds.call(self.client, n, channelo, t)
        else:
            if channel != self.client._opts.nick:
                return
            n = info.Nick(self.client, prefix)
            ch = n
            cmd = text.split(' ', 1)[0].lstrip(self.client.cmd_prefix)
            try:
                t = text.split(' ', 1)[1].strip()
            except IndexError:
                t = ''
            for cmds in self.cmds.get(cmd, []):
                cmds.call(self.client, n, ch, t)

    ### End Handlers ###
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

import sys
from collections import defaultdict
from . import utils, info
import traceback
import re

class Handler:
    def __init__(self, client):
        self.client = client
        self.hooks = defaultdict(list)
        self.orighooks = defaultdict(list)
        self.add_handler('join', self.on_join)
        self.add_handler('ping', self.on_ping)
        self.add_handler('whospcrpl',self.on_whox)
        self.add_handler('quietlist',self.on_quietlist)
        self.add_handler('banlist',self.on_banlist)     
        self.channels = info.Dct()

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

    def on_disconnect(self):
        self.hooks.update(self.orighooks)

    def recieve_raw(self, prefix, cmd, *args):
        for func in self.hooks.get(cmd, []):
            try:
                func.func(self.client, prefix, *args)
            except Exception:
                sys.stderr.write(traceback.format_exc())

    def connected(self):
        self.client.register()

    def on_join(self, cli, nick, channel):
        nick = info.Nick(nick)
        if nick.name == cli.conf.nick:
            cli.whox(channel)
            cli.banlist(channel)
            cli.quietlist(channel)

    def on_whox(self, cli, prefix, snick, numeric, channel, ident, 
        host, nick, status, account, gecos):
        if numeric != '254':
            return
        if channel not in self.channels:
            self.channels[channel] = info.Channel(channel)
        opped = '@' in status
        voiced = '*' in status
        away = 'G' in status
        acc = account if account != '0' else None
        raw = '{0}!{1}@{2}'.format(nick, ident, host)
        n = info.Nick(raw)
        self.channels[channel].users[nick] = info.ChannelUser(nick=n,
            operator=opped,account=acc,voiced=voiced,away=away)

    def on_ping(self, cli, _, text):
        cli.pong(text)

    def on_banlist(self, cli, prefix, snick, channel, ban, setter, time):
        for user in self.channels[channel].users.values():
            if user.nick.match(ban):
                user.banned = True

    def on_quietlist(self, cli, prefix, snick, channel, ban, setter, time):
        for user in self.channels[channel].users.values():
            if user.nick.match(ban):
                user.quieted = True


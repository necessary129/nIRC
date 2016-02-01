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
import sys
from collections import defaultdict
from . import utils, info
import traceback
import re
import fnmatch
import base64

class Handler:
    def init(self, client):
        self.client = client
        for f,y in utils.ret_f():
            self.client.add_attr(f,y)
        self.hooks = defaultdict(list)
        self.orighooks = defaultdict(list)
        self.channels = info.Dct()
        self.cmds = defaultdict(list)
        self.quiets = defaultdict(set)
        self.handlers_do()
        self.supported_caps = set()
        self.request_caps = set(['multi-prefix'])
        if self.client.use_sasl:
            self.request_caps.add('sasl')

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
        self.add_handler('unavailresource', self.on_nonick,125)
        self.add_handler('nicknameinuse', self.on_nonick,125)
        self.add_handler('cap', self.on_cap)
        self.add_handler('saslsuccess',self.on_sasl_success)
        self.add_handler('saslfail',self.on_sasl_failure)
        self.add_handler('sasltoolong',self.on_sasl_failure)
        self.add_handler('saslaborted',self.on_sasl_failure)
        self.add_handler('saslalready',self.on_sasl_failure)
        self.add_handler('authenticate',self.on_authenticate)
        self.add_handler('endofmotd',self.on_motd,254)
        self.add_handler('nomotd',self.on_motd,254)
        self.add_handler('nick',self.on_nick)
        self.add_handler('hosthidden',self.on_host)

    def add_handler(self, event, func, hookid=-1,nod=False):
        hook = utils.hook(func, hookid=hookid)
        self.hooks[event.lower()].append(hook)
        if not nod:
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
                self.client.error_logger(traceback.format_exc())

    def connected(self):
        self.client.cap('LS','302')
        if not self.client.use_sasl:
            self.client._send('PASS {0}:{1}'.format(self.client.nickserv_account,
             self.client.nickserv_password))
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

    def do_regain(self, *args):
        self.client._send("NS REGAIN",self.client.nick.strip('_'))

    def on_motd(self, cli, *args):
        self.client._send("NICK",self.client.nick.strip('_'))
        self.client.join(",".join(self.client.join_channels))
        self.del_handler(254)

    def on_nonick(self, *args):
        self.client._opts.nick += '_'
        self.client.snick()
        self.del_handler(125)
        self.add_handler('unavailresource', self.do_regain,nod=True)
        self.add_handler('nicknameinuse', self.do_regain,nod=True)

    #lykos ;)
    def on_cap(self, cli, svr, mynick, cmd, caps, star=None):
        if cmd == 'LS':
            if caps == '*':
                # Multi-line LS
                self.supported_caps.update(star.split())
            else:
                self.supported_caps.update(caps.split())

                if self.client.use_sasl and 'sasl' not in self.supported_caps:
                    self.client.stream_handler('Server does not support SASL authentication')
                    cli.disconnect()

                common_caps = self.request_caps & self.supported_caps

                if common_caps:
                    cli.cap('REQ', ':{0}'.format(' '.join(common_caps)))
        elif cmd == 'ACK':
            if 'sasl' in caps:
                cli._send('AUTHENTICATE PLAIN')
            else:
                cli.cap('END')
        elif cmd == 'NAK':
            # This isn't supposed to happen. The server claimed to support a
            # capability but now claims otherwise.
            cli._send('Server refused capabilities: {0}'.format(' '.join(caps)))

    def on_authenticate(self, cli, prefix, p):
        if p == '+':
            acc = self.client.nickserv_account.encode('utf8')
            passw = self.client.nickserv_password.encode('utf8')
            string = b'\0'.join((acc,acc, passw))
            auth_token = base64.b64encode(string).decode('utf8')
            cli._send('AUTHENTICATE',auth_token)

    def on_sasl_success(self, cli, *etc):
        cli.cap('END')

    def on_sasl_failure(self, cli, *etc):
        cli.stream_handler('Authentication Failed.')
        cli.disconnect()

    def on_disconnect(self):
        self.hooks.update(self.orighooks)

    def on_join(self, cli, nick, channel):
        nicka = info.Nick(self.client, nick)
        if nicka.name == cli._opts.nick:
            cli._opts.nch(nicka)
            cli.whox(channel)
            cli.banlist(channel)
            cli.quietlist(channel)
        else:
            self.channels[channel].users[nick] = info.ChannelUser(self.client, self.channels[channel], nick) 
            cli.whox(nicka.name)
            self.client.ping(':NEWUSER {0} {1}'.format(channel, nicka.name))

    def on_whox(self, cli, prefix, snick, *args):
        self.client._opts.nick = snick
        try:
            numeric, channel, ident, host, nick, status, account, gecos = args
        except ValueError:
            return
        if numeric != '254':
            return
        if (channel != '*') and (channel not in self.channels):
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
            if char in info.Modes.ArgModes:
                n += 1

    def on_nick(self, cli, prefix, nick):
        onick = prefix.split('!')[0]
        if onick == self.client.nick:
            self.client._opts.nick = nick
        for channel in self.channels.values():
            if nick in channel.users.keys():
                channel.users[nick] = channel.users[onick]
                del channel.users[onick]
                channel.users[nick].nick.name = nick

    def on_pong(self, cli, _, _1, text):
        if not text.startswith('NEWUSER'):
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

    def host_change(self, *args, **kwargs):
        pass

    def ident_change(self, *args, **kwargs):
        pass

    def on_part(self, cli, prefix, channel, msg=None):
        self.channels[channel].users.pop(prefix.split('!')[0], None)

    def on_quit(self, cli, prefix, msg=None):
        u = prefix.split('!')[0]
        for channel in self.channels.values():
            if u in channel.users:
                channel.users.pop(u)

    def on_host(self, cli, prefix, snick, host, bullshit):
        self.client._opts.host = host

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
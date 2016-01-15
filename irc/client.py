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

import asyncio
import handler.info as info
#import handler

from handler.handle import Handler

from .parser import parse_raw_irc_command

import threading
import time

class TokenBucket(object):
    """An implementation of the token bucket algorithm.

    >>> bucket = TokenBucket(80, 0.5)
    >>> bucket.consume(1)
    """
    def __init__(self, tokens, fill_rate):
        """tokens is the total tokens in the bucket. fill_rate is the
        rate in tokens/second that the bucket will be refilled."""
        self.capacity = float(tokens)
        self._tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.time()

    def consume(self, tokens):
        """Consume tokens from the bucket. Returns True if there were
        sufficient tokens otherwise False."""
        if tokens <= self.tokens:
            self._tokens -= tokens
            return True
        return False

    @property
    def tokens(self):
        now = time.time()
        if self._tokens < self.capacity:
            delta = self.fill_rate * (now - self.timestamp)
            self._tokens = min(self.capacity, self._tokens + delta)
        self.timestamp = now
        return self._tokens

def add_commands(d):
    def dec(cls):
        for c in d:
            def func(x):
                def gen(self, *a):
                    self._send(x.upper()+" "+" ".join(a))
                return gen
            setattr(cls, c, func(c))
        return cls
    return dec
@add_commands(("join",
               "mode",
               "nick",
               "who",
               "cap",
               "pong",
               "ping"))
class IRCClient(asyncio.Protocol):
    def __init__(self, **kwargs):
        asyncio.Protocol.__init__(self)
        self.handler = Handler(self)
        self.server = 'noteness.cf'
        self.port = 6667
        self._opts = info.States(self)
        self._opts.nick = kwargs.pop('nick')
        self.use_sasl = False
        self.server_pass = None
        self.ident = None
        self.nickserv_account = None
        self.nickserv_password = None
        self.__dict__.update(**kwargs)
        self.connected = False
        self.reconnect = True
        self._buffer = bytes()
        self.lock = threading.Lock()
        self.printer = lambda output, level=None: print(output)
        self.tokenbucket = TokenBucket(23, 1.73)

    def _connect(self):
        loop = asyncio.get_event_loop()
        task = asyncio.Task(loop.create_connection(
            self, self.server, self.port))
        try:
            loop.run_until_complete(task)
        except TimeoutError:
            print("Timeout")

    def connection_made(self, sock):
        self.connected = True
        self._socket = sock
        self.handler.connected()
    def connection_lost(self, exc):
        self.connected = False
        self._disconnected()

    def eof_recieved(self):
        self.connected = False
        self._disconnected()

    def _disconnected(self):
        loop = asyncio.get_event_loop()
        loop.stop()
        self.handler.on_disconnect()

    def connect(self):
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            try:
                while True:
                    self._connect()
                    loop.run_forever()
                    if not self.reconnect:
                        break
            finally:
                loop.close()

    def _send(self, *a):
        with self.lock:
            largs = []
            for x in a:
                y= str(x)
                largs.append(y.encode('utf8'))
            msg = b" ".join(largs)
            while not self.tokenbucket.consume(1):
                time.sleep(0.3)
            self.printer(msg.decode('utf8'))
            self._socket.write(msg+'\r\n'.encode('utf8'))

    def disconnect(self, msg=None):
        self._send("QUIT{0}".format(" :"+msg if msg else ""))
        self.connected = False
        self.reconnect = False
        asyncio.get_event_loop().stop()

    def banlist(self, ch):
        self.mode(ch,'b')

    def quietlist(self, ch):
        self.mode(ch,'q')

    def whox(self, ch):
        self._send("who {0} %tcuhnfra,254".format(ch))

    def data_received(self, raw):
        self._buffer += raw
        data = self._buffer.split(bytes("\n", "utf8"))
        self._buffer = data.pop()
        for el in data:
            prefix, command, args = parse_raw_irc_command(el.decode('utf8'))
            self.printer((prefix, command, args))
            self.handler.recieve_raw(prefix, command, *args)  

    def register(self):
        self.nick(self.gnick)
        self.user(self.ident, self.realname)

    def add_handler(self, event, hookid=-1):
        def reg(func):
            self.handler.add_handler(event, func, hookid)
            return func
        return reg

    def del_handler(self, *args, **kwargs):
        return self.handler.del_handler(*args, **kwargs)

    def user(self, ident, rname):
        self._send("USER", ident, self.server, self.server, ":{0}".format(rname or ident))

    def __call__(self):
        return self

    @property
    def gnick(self):
        return self._opts.nick

    def __repr__(self):
        return "{self.__class__.__name__}(Server={self.server},Port={self.port},Nick={self.gnick})".format(self=self)
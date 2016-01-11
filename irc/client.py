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
import info
#import handler


class IRCClient(asyncio.Protocol):
    def __init__(self, handler, **kwargs):
        asyncio.Protocol.__init__(self)
        self.handler = handler
        self.server = 'chat.freenode.net'
        self.port = 6667
        self.conf = info.States()
        self.state = info.States()
        self.conf.nick = kwargs.pop('nick')
        self.use_sasl = False
        self.server_pass = None
        self.ident = None
        self.nickserv_account = None
        self.nickserv_password = None
        self.__dict__.update(**kwargs)
        self.connected = False
        self.reconnect = True
        self._buffer = bytes()

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
        self._socket.write("USER Hidsaf Hi Hi Hi\r\n".encode('utf8'))
        self._socket.write("NICK Hiaaaad\r\n".encode('utf8'))

    def connection_lost(self, exc):
        self.connected = False
        loop = asyncio.get_event_loop()
        loop.stop()

    def eof_recieved(self):
        self.connected = False
        loop = asyncio.get_event_loop()
        loop.stop()

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

    def disconnect(self):
        self.connected = False
        self.reconnect = False
        asyncio.get_event_loop().stop()

    def data_received(self, raw):
        self._buffer += raw
        data = self._buffer.split(bytes("\n", "utf8"))
        self._buffer = data.pop()
        for el in data:
            print(el.decode("utf8"))

    def __call__(self):
        return self
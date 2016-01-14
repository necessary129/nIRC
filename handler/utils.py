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

class hook:
    def __init__(self, func, hookid=-1):
        self.func = func
        self.id = hookid

class cmd:
    def __init__(self, cmd, owner_only=False,admin_only=False, pm=True):
        self.name = cmd
        self.admin_only = admin_only
        self.pm = pm
        self.owner_only = owner_only

    def call(self, nick, channel, msg):
        pass

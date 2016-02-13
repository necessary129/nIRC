from nirc import IRCClient

a = IRCClient(
    nick="a",
    ident="Hi",
    realname="SE  SE",
    owner_accounts=['note*'],
    nickserv_account = 'a',
    nickserv_password = 'pass',
    use_sasl = False,
    join_channels = ['#ff']
    )

@a.cmd('hi', owner_only=True)
def c(cli, nick, channel, isch, msg):
    nick.notice("HI")

import threading
import code


shell_banner = """
This is the nIRC lib testing system.
Use a.disconnect() first
"""

def shell():
    namespace = locals()
    namespace.update(globals())
    code.interact(banner=shell_banner, local=namespace)


def launch_shell():
    threading.Thread(target=shell).start()

launch_shell()

a.connect()
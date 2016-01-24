from irc.client import IRCClient

a = IRCClient(
    nick="a",
    ident="Hi",
    realname="SE  SE",
    owner_accounts=['note*'])
@a.add_handler('endofmotd', hookid=254)
@a.add_handler('nomotd', hookid=254)
def c(cli, *args):
    cli.join("#ff")
    a.del_handler(254)

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
try:
    a.connect()
except KeyboardInterrupt:
    a.disconnect()
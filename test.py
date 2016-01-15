from irc.client import IRCClient

a = IRCClient(nick="a",ident="Hi",realname="SE  SE")
@a.add_handler('endofmotd', hookid=254)
@a.add_handler('nomotd', hookid=254)
def c(cli, *args):
    cli.join("#ff")
    a.del_handler(254)

import threading
import code


shell_banner = """Banner
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
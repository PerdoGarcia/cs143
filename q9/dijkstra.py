from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr

### Add additional imports here ###
# Hint: read the delay.csv file here

log = core.getLogger()
delayFile = "delay.csv"

### Add global variables and data preprocessing here ###


class Dijkstra(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        log.debug("Enabling Dijkstra Module")

    def _handle_ConnectionUp(self, event):
        ### Implement your logic here ###

        log.debug("Dijkstra installed on %s", dpidToStr(event.dpid))


def launch():
    """
    Starting the Dijkstra module
    """
    core.registerNew(Dijkstra)

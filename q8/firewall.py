from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple
import os
import csv

""" Add your imports here ... """


log = core.getLogger()
policyFile = f"{os.environ['HOME']}/pox/pox/misc/firewall-policies.csv"
# because there is only one policy file, we can define the Policy namedtuple here
Policy = namedtuple('Policy', ('mac_0', 'mac_1'))

### Add global variables and data preprocessing here ###

class Firewall(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        log.debug("Enabling Firewall Module")
        self.policies = self.extract_policies(policyFile)

    def extract_policies(self, policyfile):
        policy_list = []
        try:
            with open(policyfile, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mac_0 = EthAddr(row['mac_0'])
                    mac_1 = EthAddr(row['mac_1'])
                    policy_list.append(Policy(mac_0, mac_1))
                    log.debug(f"Loaded policy: {mac_0} cannot communicate with {mac_1}")
            return policy_list
        except Exception as e:
            log.error(f"Error loading firewall policies: {e}")
            return []

    def _handle_ConnectionUp(self, event):
        """Implement your logic here"""

        if not self.policies:
            log.warning("No policies loaded, firewall disabled")
            return

        for policy in self.policies:
            # Create match for blocking traffic from mac_0 to mac_1
            block_rule1 = of.ofp_match()
            block_rule1.dl_src = policy.mac_0
            block_rule1.dl_dst = policy.mac_1

            # Create match for blocking traffic from mac_1 to mac_0 (bidirectional)
            block_rule2 = of.ofp_match()
            block_rule2.dl_src = policy.mac_1
            block_rule2.dl_dst = policy.mac_0

            
            msg1 = of.ofp_flow_mod()
            msg1.match = block_rule1
            msg2 = of.ofp_flow_mod()
            msg2.match = block_rule2

            # Send the flow modification messages to the switch
            event.connection.send(msg1)
            event.connection.send(msg2)



        log.debug("Firewall rules installed on %s", dpidToStr(event.dpid))


def launch():
    # start Firewall module
    core.registerNew(Firewall)

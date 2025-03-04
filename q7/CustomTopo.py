from mininet.topo import Topo


class CustomTopo(Topo):
    """
    Simple Data Center Topology

    linkopts# - link parameters (where #: 1: core, 2: aggregation, 3: edge)
    fanout - number of child switches per parent switch
    """

    def __init__(self, linkopts1, linkopts2, linkopts3, fanout=2, **opts):
        """Initialize topology and default options"""
        Topo.__init__(self, **opts)
        # Topo: the base class for Mininet topologies
        """ Implement your logic here """


        # (binary tree) For each aggregation layers there are two edges, where each edge has 2 hosts
        # not actually 2 but n fanout based on the input
        # so add aggregation, and for each aggregation add edge switches, and for each edge add hosts
        # Root is some core
        core = self.addSwitch('c1')

        aggr_switches = []
        for i in range(fanout):
            aggr_switch = self.addSwitch('a%s' % (i + 1))
            aggr_switches.append(aggr_switch)
            self.addLink(core, aggr_switch, **linkopts1)

        edge_switches = []
        for i, aggr_switch in enumerate(aggr_switches):
            for j in range(fanout):
                edge_switch = self.addSwitch('e%s' % (i * fanout + j + 1))
                edge_switches.append(edge_switch)
                self.addLink(aggr_switch, edge_switch, **linkopts2)

        # host = []

        host_count = 1
        for i, edge_switch in enumerate(edge_switches):
            for j in range(fanout):
                host = self.addHost('h%s' % host_count)
                self.addLink(edge_switch, host, **linkopts3)
                host_count += 1

topos = {"custom": (lambda: CustomTopo())}

# Uncomment below (or write your own code) to test your topology ##
linkopts1 = dict(bw=10, delay="5ms", loss=10, max_queue_size=1000, use_htb=True)
linkopts2 = dict(bw=10, delay="5ms", loss=10, max_queue_size=1000, use_htb=True)
linkopts3 = dict(bw=10, delay="5ms", loss=10, max_queue_size=1000, use_htb=True)
topos = { "custom": ( lambda: CustomTopo(linkopts1,linkopts2,linkopts3) ) }

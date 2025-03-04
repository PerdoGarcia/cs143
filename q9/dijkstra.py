from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
import csv
import heapq

### Add additional imports here ###
# Hint: read the delay.csv file here

log = core.getLogger()
delayFile = "delay.csv"

"""

Find shortest path from h13 to h15

 Treat the source as s12 (since h13 is directly attached to s12).

 Initialize distances to ∞ for all switches:
   distance[s11] = ∞
   distance[s12] = 0    # source
   distance[s14] = ∞
   distance[s16] = ∞
   distance[s18] = ∞

 Mark all switches as unvisited.
   unvisited = {s11, s12, s14, s16, s18}

 Pick the unvisited node with the smallest distance.
   Start with s12 (distance[s12] = 0).

From s12, update neighbors:
   - s11 via link k (30 ms) => distance[s11] = 30
   - s14 via link h (50 ms) => distance[s14] = 50
   - s18 via link m (100 ms) => distance[s18] = 100
   Mark s12 is visited.

 Next smallest unvisited node is s11 (distance 30).
   - s11 only connects back to s12, which is visited. No updates.
   Mark s11 is visited.

Next smallest unvisited node is s14 (distance 50).
   - Once we pick s14,  essentially reached the destinations switch
 The distance to s14 is 50 ms, so the total delay from s12 to s14 is 50 ms.

9. Hence, the path is:
   h13 -> s12 -> s14 -> h15 and the total delay is 50 ms (the link s12 - s14 has 50 ms; host links are 0 ms).

# too much work to do this manually, so we will use dijkstra's algorithm for the rest of the paths
Shortest paths from each host to every other host:
h13 -> h15: s12-> s14-> h15 = 50 ms
h13-> h17: s12-> s14-> s16-> h17 = 60 ms
h13-> h19: s12-> s14-> s18-> h19 = 70 ms
h15-> h17: s14-> s16-> h17 = 10 ms
h15-> h19: s14-> s18-> h19 = 20 ms
h17-> h19: s16-> s18-> h19 = 30 ms (or s16-> s14-> s18-> h19, also 30 ms)

"""
class Q9Topo(Topo):
    def __init__(self, **opts):
        super(Q9Topo, self).__init__(**opts)

        # Switches
        s11 = self.addSwitch('s11')
        s12 = self.addSwitch('s12')
        s14 = self.addSwitch('s14')
        s16 = self.addSwitch('s16')
        s18 = self.addSwitch('s18')

        # Hosts
        h13 = self.addHost('h13')
        h15 = self.addHost('h15')
        h17 = self.addHost('h17')
        h19 = self.addHost('h19')

        # Switch-switch links
        self.addLink(s11, s12, key='k')
        self.addLink(s12, s14, key='h')
        self.addLink(s12, s18, key='m')
        self.addLink(s14, s16, key='i')
        self.addLink(s16, s18, key='j')
        self.addLink(s14, s18, key='n')

        # Host-switch links (assume 0 ms if no key)
        self.addLink(s12, h13)
        self.addLink(s14, h15)
        self.addLink(s16, h17)
        self.addLink(s18, h19)

class Dijkstra(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        log.debug("Enabling Dijkstra Module")

        self.delays = {}
        self.graph = {}
        self.ports = {}
        self.shortest_paths = {}

        self.host_macs = {
            'h13': '00:00:00:00:00:13',
            'h15': '00:00:00:00:00:15',
            'h17': '00:00:00:00:00:17',
            'h19': '00:00:00:00:00:19'
        }

        self.read_delays()
        topology = Q9Topo()
        self.build_graph(topology)

    def read_delays(self):
        try:
            with open(delayFile, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    link_label = row['link']
                    delay_val = int(row['delay'])
                    self.delays[link_label] = delay_val
            log.debug("Delays read from %s: %s", delayFile, self.delays)
        except IOError:
            log.error("Could not read delay file: %s", delayFile)

    def build_graph(self, topo):
        """
        Build an adjacency list (self.graph) for all nodes (switches + hosts),
        plus a parallel structure (self.ports) to store which port connects each node pair.
        """
        # Initialize adjacency for all nodes
        for node in topo.nodes():
            self.graph[node] = {}
            self.ports[node] = {}

        # For each link, get the link info and ports
        for (n1, n2) in topo.links():
            # port(n1, n2) -> (port_n1, port_n2)
            (p1, p2) = topo.port(n1, n2)
            self.ports[n1][n2] = p1
            self.ports[n2][n1] = p2

            link_data = topo.linkInfo(n1, n2)
            link_key = link_data.get('key')
            if link_key and link_key in self.delays:
                delay = self.delays[link_key]
            else:
                delay = 0

            self.graph[n1][n2] = delay
            self.graph[n2][n1] = delay

        log.debug("Graph built: %s", self.graph)
        log.debug("Ports mapping: %s", self.ports)

    #
    # Dijkstra + path reconstruction
    #
    def dijkstra(self, start):
        dist = {}
        prev = {}
        for node in self.graph:
            dist[node] = float('inf')
            prev[node] = None
        dist[start] = 0

        pq = [(0, start)]
        visited = set()

        while pq:
            current_dist, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            for v, link_delay in self.graph[u].items():
                alt = current_dist + link_delay
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(pq, (alt, v))

        return dist, prev

    def reconstruct_path(self, prev, target):
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = prev[current]
        path.reverse()
        return path

    #
    # Install flow rules for a single path from src -> dst
    #
    def install_path_flows(self, src, dst, path):

        if len(path) < 2:
            return

        # If dst is a host in our known map, get its MAC
        dst_mac = self.host_macs.get(dst, None)

        # to path
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i+1]

            if current_node.startswith('s'):
                # find the output port port to next node
                out_port = self.ports[current_node][next_node]

                # build a flow_mod
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match()

                if dst_mac:
                    # get MAC dst
                    msg.match.dl_dst = EthAddr(dst_mac)
                else:
                    #dunno
                    pass

                msg.actions.append(of.ofp_action_output(port = out_port))

                sw_dpid = self._name_to_dpid(current_node)
                con = core.openflow.getConnection(sw_dpid)
                if con:
                    log.info("Installing flow on %s (dpid=%s) for traffic to %s -> out port %s",
                             current_node, dpidToStr(sw_dpid), dst, out_port)
                    con.send(msg)

    def _name_to_dpid(self, switch_name):
        """
        """
        # remove the 's' prefix and parse as integer
        if switch_name.startswith('s'):
            try:
                num = int(switch_name[1:])
                return num
            except:
                pass
        # if we can't parse, return 0
        return 0

    def _handle_ConnectionUp(self, event):
        """
        Called when a switch connects to the controller.
        We compute all-pairs shortest paths and install flows for host->host pairs.
        """
        log.debug("Switch %s has connected", dpidToStr(event.dpid))

        # populate shortest paths
        self.shortest_paths = {}
        for src in self.graph:
            dist, prev = self.dijkstra(src)
            self.shortest_paths[src] = {}
            for dst in self.graph:
                if src == dst:
                    continue
                path = self.reconstruct_path(prev, dst)
                cost = dist[dst]
                self.shortest_paths[src][dst] = (path, cost)

        # hard coded hosts
        hosts = ['h13', 'h15', 'h17', 'h19']
        for h_src in hosts:
            for h_dst in hosts:
                if h_src == h_dst:
                    continue
                if h_src in self.shortest_paths and h_dst in self.shortest_paths[h_src]:
                    path, cost = self.shortest_paths[h_src][h_dst]
                    log.info("Path %s -> %s = %s, cost = %s", h_src, h_dst, path, cost)
                    # Install flows along this path
                    self.install_path_flows(h_src, h_dst, path)

def launch():
    core.registerNew(Dijkstra)

from mininet.topo import Topo


class Q9Topo(Topo):
    def __init__(self, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        ### Implement your logic here ###


topos = {"custom": (lambda: Q9Topo())}

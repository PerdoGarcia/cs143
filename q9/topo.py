from mininet.topo import Topo


class Q9Topo(Topo):
    def __init__(self, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        ### Implement your logic here ###
        # I dont know if there is a more robust way to do this
        # Add switches
        s11 = self.addSwitch('s11')
        s12 = self.addSwitch('s12')
        s14 = self.addSwitch('s14')
        s16 = self.addSwitch('s16')
        s18 = self.addSwitch('s18')

        # Add hosts
        h13 = self.addHost('h13')
        h15 = self.addHost('h15')
        h17 = self.addHost('h17')
        h19 = self.addHost('h19')

        # Add links between switches
        # Links labeled with their corresponding letters from the image
        self.addLink(s11, s12, cls=None, **{'key': 'k'})
        self.addLink(s12, s14, cls=None, **{'key': 'h'})
        self.addLink(s12, s18, cls=None, **{'key': 'm'})
        self.addLink(s14, s16, cls=None, **{'key': 'i'})
        self.addLink(s16, s18, cls=None, **{'key': 'j'})
        self.addLink(s14, s18, cls=None, **{'key': 'n'})

        # Add links to hosts
        self.addLink(s12, h13)
        self.addLink(s14, h15)
        self.addLink(s16, h17)
        self.addLink(s18, h19)

topos = {"custom": (lambda: Q9Topo())}

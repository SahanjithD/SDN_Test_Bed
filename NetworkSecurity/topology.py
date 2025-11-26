from mininet.topo import Topo

class SeniorProjectTopo(Topo):
    def build(self):
        # Create two switches (mimicking the RPi boards)
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Create two hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Add links (Mimicking the Ethernet cables)
        self.addLink(h1, s1)
        self.addLink(s1, s2)
        self.addLink(s2, h2)

topos = { 'senior_topo': ( lambda: SeniorProjectTopo() ) }


##Run this with: sudo mn --custom topology.py --topo senior_topo --controller=remote
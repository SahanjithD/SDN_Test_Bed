#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import RemoteController

class LoadBalancerTopo(Topo):
    "Single switch connected to a client and 3 servers for Load Balancing demo."
    def build(self):
        s1 = self.addSwitch('s1')
        
        # Client
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        
        # Servers
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)

if __name__ == '__main__':
    setLogLevel('info')
    topo = LoadBalancerTopo()
    # Connect to the remote controller (Ryu)
    # Ensure your Ryu app is running on port 6633 (default)
    c1 = RemoteController('c1', ip='127.0.0.1', port=6633)
    net = Mininet(topo=topo, controller=c1)
    net.start()
    print("Topology started.")
    print("Client: h1 (10.0.0.1)")
    print("Servers: h2 (10.0.0.2), h3 (10.0.0.3), h4 (10.0.0.4)")
    print("Virtual IP: 10.0.0.100")
    print("Use 'h1 ping 10.0.0.100' to test load balancing.")
    CLI(net)
    net.stop()

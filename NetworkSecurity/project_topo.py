#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import OVSSwitch, RemoteController

class SeniorProjectTopo(Topo):
    "5 switches connected linearly with one host per switch."
    def build(self):
        switches = []

        # Loop to create 5 switches and 5 hosts
        for i in range(1, 6):
            # 1. Create Switch with specific DPID (safe for Ryu)
            # This creates IDs like "0000000000000001", "0000000000000002"
            dpid_val = f"{i:016d}" 
            s = self.addSwitch(f's{i}', dpid=dpid_val, protocols='OpenFlow13')
            switches.append(s)

            # 2. Create Host
            # IPs: 10.0.0.1, 10.0.0.2 ... (Same Subnet)
            # MACs: 00:00:00:00:00:01, ...
            h = self.addHost(
                f'h{i}',
                mac=f"00:00:00:00:00:{i:02d}",
                ip=f"10.0.0.{i}/24"
            )
            
            # 3. Link Host to its Switch (e.g., h1-s1)
            self.addLink(h, s)

        # 4. Connect Switches Linearly (s1-s2, s2-s3, s3-s4, s4-s5)
        for i in range(len(switches) - 1):
            self.addLink(switches[i], switches[i + 1])

if __name__ == '__main__':
    setLogLevel('info')

    # Initialize Topology
    topo = SeniorProjectTopo()

    # Define Remote Controller (Ryu)
    c1 = RemoteController('c1', ip='127.0.0.1', port=6653)

    # Initialize Network
    net = Mininet(topo=topo, controller=c1, switch=OVSSwitch)

    print("*** Starting Network")
    net.start()
    
    # Wait until all switches connect to the controller
    try:
        net.waitConnected(timeout=10)
        print("*** Controller connection: SUCCESS (all switches connected)")
    except Exception:
        print("*** Controller connection: TIMEOUT/FAILED (switches not fully connected)")
    
    print("*** Testing Connectivity (Ping All)")
    net.pingAll()
    
    print("*** Running CLI")
    CLI(net)
    
    print("*** Stopping Network")
    net.stop()
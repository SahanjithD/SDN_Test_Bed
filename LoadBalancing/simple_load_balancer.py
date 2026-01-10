from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4

class SimpleLoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleLoadBalancer, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        
        # Virtual IP and MAC for the service
        self.virtual_ip = "10.0.0.100"
        self.virtual_mac = "00:00:00:00:00:FE"
        
        # Server details (IP, MAC, Port)
        # Note: In Mininet with the provided topology:
        # h1 is on port 1
        # h2 is on port 2
        # h3 is on port 3
        # h4 is on port 4
        self.servers = [
            {'ip': '10.0.0.2', 'mac': '00:00:00:00:00:02', 'port': 2},
            {'ip': '10.0.0.3', 'mac': '00:00:00:00:00:03', 'port': 3},
            {'ip': '10.0.0.4', 'mac': '00:00:00:00:00:04', 'port': 4},
        ]
        self.server_index = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst = eth.dst
        src = eth.src

        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][src] = in_port
        
        # Handle ARP for Virtual IP
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocols(arp.arp)[0]
            if arp_pkt.dst_ip == self.virtual_ip and arp_pkt.opcode == arp.ARP_REQUEST:
                self.logger.info("ARP request for VIP %s", self.virtual_ip)
                # Reply with Virtual MAC
                self.send_arp_reply(datapath, eth, arp_pkt, in_port)
                return

        # Handle IP traffic
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocols(ipv4.ipv4)[0]
            
            # 1. Client to VIP (Load Balancing)
            if ip_pkt.dst == self.virtual_ip:
                actions = [
                    parser.OFPActionSetField(eth_dst=server['mac']),
                    parser.OFPActionSetField(ipv4_dst=server['ip']),
                    parser.OFPActionOutput(server['port'])
                ]
                # self.add_flow(datapath, 10, match, actions)
                
                # Send the packet out immediatelydst=server['mac']),
                    parser.OFPActionSetField(ipv4_dst=server['ip']),
                    parser.OFPActionOutput(server['port'])
                ]
                self.add_flow(datapath, 10, match, actions)
                
                # Send the packet out immediately
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
                return

            # 2. Server to Client (Reverse NAT)
            # Check if source is one of our servers
            is_server_response = False
            for server in self.servers:
                if ip_pkt.src == server['ip']:
                    is_server_response = True
                    break
            
            if is_server_response:
                # We need to rewrite SRC IP/MAC to VIP/VMAC so client accepts it
                # We also need to know where to send it (Client Port).
                # We can use the learned mac_to_port table.
                
                dst = eth.dst
                
                # If we know where the client is
                if dst in self.mac_to_port[datapath.id]:
                    out_port = self.mac_to_port[datapath.id][dst]
                else:
                    out_port = ofproto.OFPP_FLOOD
                
                actions = [
                    parser.OFPActionSetField(eth_src=self.virtual_mac),
                    parser.OFPActionSetField(ipv4_src=self.virtual_ip),
                    parser.OFPActionOutput(out_port)
                ]
                
                if out_port != ofproto.OFPP_FLOOD:
                    match = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype, 
                                            ipv4_src=ip_pkt.src, ipv4_dst=ip_pkt.dst)
                    self.add_flow(datapath, 10, match, actions)
                
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                            in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
        # Standard Learning Switch Behavior for other traffic
        # dst = eth.dst  <-- Already extracted
        # src = eth.src  <-- Already extracted

        # self.mac_to_port.setdefault(datapath.id, {}) <-- Already done
        # self.mac_to_port[datapath.id][src] = in_port <-- Already done

        if dst in self.mac_to_port[datapath.id]:port

        if dst in self.mac_to_port[datapath.id]:
            out_port = self.mac_to_port[datapath.id][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def send_arp_reply(self, datapath, eth, arp_pkt, in_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Create ARP reply
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=eth.ethertype,
                                           dst=eth.src,
                                           src=self.virtual_mac))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=self.virtual_mac,
                                 src_ip=self.virtual_ip,
                                 dst_mac=arp_pkt.src_mac,
                                 dst_ip=arp_pkt.src_ip))
        pkt.serialize()
        
        actions = [parser.OFPActionOutput(in_port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER, actions=actions,
                                  data=pkt.data)
        datapath.send_msg(out)

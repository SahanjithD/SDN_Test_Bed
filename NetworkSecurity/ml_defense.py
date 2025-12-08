from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.lib import hub
from ryu.lib.packet import packet, ethernet, ether_types  # <--- Added ether_types
import joblib
import numpy as np
import os
import warnings

# Silence AI warnings for cleaner output
warnings.filterwarnings("ignore")

class MLDefenseL2(simple_switch_13.SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(MLDefenseL2, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.blocked_macs = set()
        self.monitor_thread = hub.spawn(self._monitor)
        
        # Load Model
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'ddos_model.pkl')
        print(f"Loading Model from: {model_path}")
        try:
            self.clf = joblib.load(model_path)
            print(">> Model Loaded. Dashboard Mode Active.")
        except:
            print("ERROR: Model not found. Defense Disabled.")

    # --- HANDSHAKE ---
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info(f">> Switch Registered: {datapath.id}")
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info(f">> Switch Disconnected: {datapath.id}")
                del self.datapaths[datapath.id]

    # --- MONITOR LOOP ---
    def _monitor(self):
        while True:
            for dp in list(self.datapaths.values()):
                req = dp.ofproto_parser.OFPFlowStatsRequest(dp)
                dp.send_msg(req)
            hub.sleep(2)

    # --- PACKET HANDLER ---
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # === FIX: Prevent Topology Flooding ===
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        # ======================================
        
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions, msg.buffer_id)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    # --- STATS HANDLER (DASHBOARD STYLE) ---
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        for stat in ev.msg.body:
            # Skip Table Miss
            if stat.priority == 0: continue

            # Features
            rate = 0
            if stat.duration_sec > 0:
                rate = stat.byte_count / stat.duration_sec
            
            pkt_rate = 0
            if stat.duration_sec > 0:
                pkt_rate = stat.packet_count / stat.duration_sec
                
            pkt_size = 0
            if stat.packet_count > 0:
                pkt_size = stat.byte_count / stat.packet_count

            # Threshold: Ignore idle/background noise (<5 pps)
            if pkt_rate < 5: continue

            try:
                features = np.array([[pkt_rate, rate, pkt_size, stat.packet_count, stat.byte_count]])
                prediction = self.clf.predict(features)
            except:
                continue
            
            src_mac = stat.match.get('eth_src', 'Unknown')

            # --- DECISION LOGIC ---
            if prediction[0] == 0:
                self.logger.info(f"   [MONITOR] Src: {src_mac} | Rate: {pkt_rate:>5.0f} pps | Size: {pkt_size:>4.0f} B | Verdict: NORMAL")
            
            else:
                if src_mac != 'Unknown' and src_mac not in self.blocked_macs:
                    self.logger.warning(f"")
                    self.logger.warning(f"!!! ------------------------------------------ !!!")
                    self.logger.warning(f"!!! ⚠ ATTACK DETECTED FROM {src_mac} !!!")
                    self.logger.warning(f"!!! Rate: {pkt_rate:.0f} pps | Size: {pkt_size:.0f} Bytes")
                    self.logger.warning(f"!!! ACTION: BLOCKING HOST")
                    self.logger.warning(f"!!! ------------------------------------------ !!!")
                    self.logger.warning(f"")
                    
                    self.block_host(src_mac)
                    self.blocked_macs.add(src_mac)

    def block_host(self, src_mac):
        self.logger.info(f"   [DEFENSE] applying GLOBAL BLOCK on {src_mac}")
        
        # LOOP through ALL switches (s1, s2, s3, s4, s5)
        for dp in self.datapaths.values():
            parser = dp.ofproto_parser
            match = parser.OFPMatch(eth_src=src_mac)
            
            # Add Flow: Priority 100, Actions=[] (Drop)
            mod = parser.OFPFlowMod(
                datapath=dp, 
                priority=100, 
                match=match, 
                instructions=[]
            )
            dp.send_msg(mod)
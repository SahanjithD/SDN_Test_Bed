from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.lib import hub
import joblib
import numpy as np
import os
import json

class MLDefense(simple_switch_13.SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(MLDefense, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.blocked_ips = set()
        self.last_counts = {}
        self.rate_threshold = 1000  # pps threshold to reduce noise
        self.monitor_thread = hub.spawn(self._monitor)
        
        # Load Model
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'ddos_model.pkl')
        print(f"Loading Model from: {model_path}")
        try:
            self.clf = joblib.load(model_path)
        except Exception as e:
            self.logger.error(f"Failed to load model at {model_path}: {e}")
            raise
        print("Model Loaded. Debug Mode Active.")

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
                self.logger.info(f"Datapath joined: {datapath.id}")
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]
                self.logger.info(f"Datapath left: {datapath.id}")

    def _monitor(self):
        while True:
            for dp in list(self.datapaths.values()):
                req = dp.ofproto_parser.OFPFlowStatsRequest(dp)
                dp.send_msg(req)
            hub.sleep(2)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        for stat in ev.msg.body:
            # Skip table-miss and default high priorities to reduce noise
            if stat.priority in (0, 65535):
                continue

            # Calculate Features
            rate = 0
            if stat.duration_sec > 0:
                rate = stat.byte_count / stat.duration_sec
            
            pkt_rate = 0
            if stat.duration_sec > 0:
                pkt_rate = stat.packet_count / stat.duration_sec
                
            pkt_size = 0
            if stat.packet_count > 0:
                pkt_size = stat.byte_count / stat.packet_count

            # Debounce: only act if packet_count increased since last read
            try:
                match_json = stat.match.to_jsondict()
                match_str = json.dumps(match_json, sort_keys=True)
            except Exception:
                match_str = str(stat.match)
            key = (ev.msg.datapath.id, getattr(stat, 'table_id', 0), stat.priority, match_str)
            last = self.last_counts.get(key, 0)
            if stat.packet_count <= last:
                continue
            self.last_counts[key] = stat.packet_count

            # Basic rate threshold to avoid logging idle flows
            if pkt_rate < self.rate_threshold:
                continue

            # Prepare for AI with feature names to silence sklearn warning
            try:
                import pandas as pd
                features = pd.DataFrame([
                    {
                        'packet_rate': pkt_rate,
                        'byte_rate': rate,
                        'packet_size': pkt_size,
                        'packet_count': stat.packet_count,
                        'byte_count': stat.byte_count,
                    }
                ])
            except Exception:
                features = np.array([[pkt_rate, rate, pkt_size, stat.packet_count, stat.byte_count]])
            prediction = self.clf.predict(features)
            
            # Limited DEBUG PRINT to reduce spam
            status = "NORMAL" if prediction[0] == 0 else "ATTACK"
            self.logger.info(f"Flow prio={stat.priority} pkts={stat.packet_count} rate={pkt_rate:.0f} size={pkt_size:.0f} -> {status}")

            # MITIGATION
            if prediction[0] == 1 and stat.priority > 0:
                src_ip = stat.match.get('ipv4_src', 'Unknown')
                self.logger.warning(f"ATTACK DETECTED src={src_ip} size={pkt_size:.0f}B rate={pkt_rate:.0f}pps")
                if src_ip != 'Unknown' and src_ip not in self.blocked_ips:
                    self.block_host(ev.msg.datapath, src_ip)
                    self.blocked_ips.add(src_ip)

    def block_host(self, datapath, src_ip):
        parser = datapath.ofproto_parser
        if src_ip == 'Unknown': return
        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip)
        mod = parser.OFPFlowMod(datapath=datapath, priority=100, match=match, instructions=[])
        datapath.send_msg(mod)
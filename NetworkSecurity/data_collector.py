import csv
import os
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.lib import hub
from operator import attrgetter

class DataCollector(simple_switch_13.SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(DataCollector, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.file_name = "traffic_data.csv"
        
        # 1. Create CSV
        if not os.path.exists(self.file_name):
            print(f"Creating new file: {self.file_name}")
            with open(self.file_name, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['packet_count', 'byte_count', 'duration_sec', 'byte_rate', 'label'])
        
        # LABEL: 0 = Normal, 1 = Attack
        self.current_label = 1 

    # --- THIS WAS MISSING: REGISTERS SWITCHES SO WE CAN QUERY THEM ---
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                print(f"Switch Registered: {datapath.id}")
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                print(f"Switch Disconnected: {datapath.id}")
                del self.datapaths[datapath.id]
    # ---------------------------------------------------------------

    def _monitor(self):
        while True:
            # print(f"Polling {len(self.datapaths)} switches...")
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(2)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        saved_count = 0
        for stat in ev.msg.body:
            
            # Allow seeing Priority 0 for debugging connectivity
            # if stat.priority == 0: continue
            
            pkt_count = stat.packet_count
            byte_count = stat.byte_count
            duration = stat.duration_sec
            
            rate = 0
            if duration > 0:
                rate = byte_count / duration
            
            # Write to CSV
            with open(self.file_name, 'a') as f:
                writer = csv.writer(f)
                writer.writerow([pkt_count, byte_count, duration, rate, self.current_label])
            
            saved_count += 1
            print(f"SAVED ROW: Pkts={pkt_count}, Label={self.current_label}")
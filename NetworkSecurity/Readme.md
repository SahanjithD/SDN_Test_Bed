# DDoS Defense

## Part 1: Mininet

### Topology Design

A linear topology consisting of 5 switches and 5 hosts was constructed using a Python script (project_topo.py).


### Data Collection

To train an ML model, traffic statistics had to be captured. A Ryu application (data_collector.py) was developed to listen to flow statistics.

nitial Challenge: Raw statistics (Byte Count, Packet Count) were insufficient for distinguishing attacks from heavy downloads.

Solution: Feature Engineering was applied. New metrics were calculated dynamically:

    Packet Rate (pps): Distinguishes high-frequency floods from normal traffic.

    Packet Size (Avg Bytes): Distinguishes small malicious packets from large data packets.

Data Generation: Two distinct datasets were generated:

    Normal Traffic: Generated using iperf (bandwidth tests) and ping.

    Attack Traffic: Generated using hping3 to simulate a UDP Flood.



### Model Training & Accuracy Refinement


A Random Forest Classifier was selected

Initial training yielded only ~67% accuracy. It was discovered that "noise" from the network (ARP requests, control packets) was confusing the model.


The Fix: A filter was added to the training script (train_model.py) to ignore flows with fewer than 10 packets.


Result: Accuracy increased to 93.23%, with a clear distinction learned between large normal packets (~5KB) and tiny attack packets (~73B).


## Part 2 : The Defense Logic

With the model trained (ddos_model.pkl), the real-time defense application (ml_defense_l2.py) was developed.

### Layer 2 Implementation

A decision was made to implement the defense at Layer 2 (MAC Address level) to simplify the logic and avoid complexities with IP/ARP parsing. The controller was programmed to


Monitor all active flows every 2 seconds.

Extract flow features (Rate, Size).

Query the AI Model for a verdict.

If "ATTACK" is predicted, a high-priority (Priority 100) DROP rule is installed against the source MAC address.


### The "Silence" Bug

During initial testing, the controller terminal remained blank despite active attacks.

    Cause: A logic threshold (if pkt_rate < 500) was too high for the simulation environment.

    Resolution: The threshold was lowered to 10 pps for testing purposes, allowing the logs to populate immediately.






# How...

```bash
# 1. Collect Data (Edit data_collector.py label 0 then 1)
ryu-manager data_collector.py
sudo python3 project_topo.py

# 2. Train Model
python3 train_model.py
```

```bash
#flood UDP packets
h3 hping3 --flood --udp -p 80 10.0.0.1
```



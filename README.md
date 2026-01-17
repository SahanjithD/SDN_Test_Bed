# SDN Test Bed

A comprehensive Software-Defined Networking (SDN) test bed featuring OpenFlow controllers, load balancing, and ML-based DDoS defense mechanisms. Built with Ryu SDN controller, Open vSwitch (OVS), and Mininet for network simulation.

## 📋 Project Overview

This project demonstrates practical implementations of SDN concepts including:
- **Load Balancing**: Round-robin load balancer with virtual IP(not fully implemented)
- **Network Security**: ML-based DDoS detection and mitigation using flow statistics
- **Network Topologies**: Various Mininet topology configurations for testing
- **OpenFlow Management**: Configuration and management of OpenFlow switches

## 🗂️ Project Structure

### `/LoadBalancing` (not fully implemented)
Round-robin load balancing application for distributing traffic across multiple servers.

**Files:**
- `simple_load_balancer.py`: Ryu application implementing load balancing logic
- `lb_topo.py`: Mininet topology (1 client, 3 servers, 1 switch)

**Quick Start:**
```bash
# Terminal 1: Start Ryu controller
ryu-manager LoadBalancing/simple_load_balancer.py

# Terminal 2: Start Mininet topology
sudo python3 LoadBalancing/lb_topo.py

# In Mininet CLI:
mininet> h1 ping 10.0.0.100
```

### `/NetworkSecurity`
ML-based DDoS defense system that learns to distinguish normal traffic from attack patterns.

**Key Components:**
- `data_collector.py`: Collects flow statistics from switches
- `train_model.py`: Trains Random Forest classifier on collected data
- `ml_defense.py`: Real-time defense application that detects and blocks attacks
- `project_topo.py`: Linear topology (5 switches, 5 hosts) for testing
- `traffic_data.csv`: Pre-collected traffic statistics
- `ddos_model.pkl`: Pre-trained ML model

**Features:**
- Feature engineering: Packet rate (pps) and average packet size
- 93%+ accuracy in distinguishing normal traffic from UDP floods
- Layer 2 (MAC address) defense implementation
- Real-time flow monitoring and dynamic rule installation

**Quick Start:**
```bash
# Terminal 1: Start defense controller
ryu-manager NetworkSecurity/ml_defense.py

# Terminal 2: Start topology
sudo python3 NetworkSecurity/project_topo.py

# In Mininet CLI:
mininet> h1 ping h5  # Normal traffic
mininet> h3 hping3 --flood --udp -p 80 10.0.0.5  # Attack simulation
```

**Training New Model:**
```bash
# Terminal 1: Collect normal traffic data
ryu-manager NetworkSecurity/data_collector.py
sudo python3 NetworkSecurity/project_topo.py

# Generate normal traffic with iperf/ping
# Change label in data_collector.py to 1 and repeat for attack traffic

# Terminal 3: Train model
python3 NetworkSecurity/train_model.py
```

### `/mn_Topologies`
Collection of Mininet topology templates for various testing scenarios.

**Files:**
- `1.single.py`: Single switch with multiple hosts
- `2.linear.py`: Linear chain of switches
- `3.ring.py`: Ring topology with multiple switches
- `4.run_cmds.py`: Utility for running commands on topology nodes
- `5.link_changes.py`: Demonstrates dynamic link changes
- `traditional_switch.py`: Traditional L2 learning switch

## 🛠️ System Requirements

### Software Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.9+ | Core runtime (Python 3.12 has compatibility issues) |
| **Ryu Controller** | 4.34 | OpenFlow controller framework |
| **eventlet** | 0.30.2 | Async networking library for Ryu |
| **dnspython** | 1.16.0 | DNS query support |
| **Mininet** | Latest | Network simulation platform |
| **Open vSwitch** | Latest | OpenFlow switch implementation |

### Hardware Requirements

- **Linux System**: Ubuntu
-**SDN Switches**: Raspberry pi 4B 4GB
- **Network Adapters**: For physical SDN switch integration (Raspberry Pi + USB adapters)
- **Conections** : CAT5 LAN Cables

## 🚀 Installation

### 1. Install Python 3.9 (if using Python 3.12)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.9 python3.9-venv -y
```

### 2. Create Virtual Environment

```bash
python3.9 -m venv sdn_venv
source sdn_venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip and setuptools
pip install --upgrade pip
pip install setuptools==58.0.4
pip install wheel

# Install Ryu and dependencies
pip install ryu==4.34 eventlet==0.30.2 dnspython==1.16.0

# Install additional dependencies
pip install mininet scikit-learn pandas numpy
```

### 4. Install System Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential libssl-dev libelf-dev \
                   linux-headers-$(uname -r) \
                   openvswitch-switch openvswitch-common \
                   python3-pip git mininet
```

## 🔧 Hardware Setup

For setting up a physical SDN switch using Raspberry Pi:

### On Raspberry Pi:

```bash
# Install OVS
sudo apt install -y openvswitch-switch openvswitch-common

# Create OVS bridge
sudo ovs-vsctl add-br br0

# Add physical interface to bridge
sudo ovs-vsctl add-port br0 eth0

# Assign static IP
sudo ip a add 192.168.10.3/24 dev br0
sudo ip link set br0 up

# Connect to controller (adjust controller IP as needed)
sudo ovs-vsctl set-controller br0 tcp:192.168.10.2:6653

# Configure bridge for stability
sudo ovs-vsctl set bridge br0 rstp_enable=true
sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000002
sudo ovs-vsctl set-fail-mode br0 standalone
```

### On Controller Machine:

```bash
# Ensure firewall is disabled or properly configured
sudo ufw disable  # or configure firewall rules

# Run Ryu controller
ryu-manager ryu.app.simple_switch_13
```

## 📊 Use Cases

### 1. Load Balancing Testing (not fully implemented)
- Test round-robin distribution across multiple servers
- Monitor traffic distribution in real-time
- Evaluate latency and throughput

### 2. DDoS Detection and Mitigation
- Train ML model on normal traffic patterns
- Simulate UDP flood attacks
- Verify detection accuracy and response time
- Analyze feature importance

### 3. Network Topology Experimentation
- Test different topology designs
- Study convergence behavior
- Analyze traffic patterns under various topologies

## 📝 Configuration Files

### Key Configuration Points

**LoadBalancing/simple_load_balancer.py:**
- Virtual IP: `10.0.0.100`
- Server backend addresses: `10.0.0.2`, `10.0.0.3`, `10.0.0.4`
- Modify for different VIP or server configurations

**NetworkSecurity/ml_defense.py:**
- Monitoring interval: 2 seconds (line for `req_stats`)
- Attack detection threshold: Packet rate < 10 pps or size < 100 bytes
- Priority level: 100 (high priority for attack rules)

**NetworkSecurity/data_collector.py:**
- Label: 0 for normal traffic, 1 for attack traffic
- Statistics collection interval: 2 seconds

## 🔍 Troubleshooting

### Ryu Installation Issues

**Error:** `error: Error: Setup script exited with setuptools.build_meta:__legacy__`

**Solution:** Downgrade setuptools before installing Ryu:
```bash
pip install setuptools==58.0.4
pip install ryu==4.34
```

### Python 3.12 Compatibility

**Error:** eventlet or Ryu compatibility errors with Python 3.12

**Solution:** Use Python 3.9:
```bash
python3.9 -m venv sdn_venv
source sdn_venv/bin/activate
```

### Network Connectivity

**Issue:** Controller cannot connect to switch

**Solutions:**
- Verify firewall is disabled: `sudo ufw disable`
- Check bridge is up: `sudo ip link set br0 up`
- Verify static IPs are assigned correctly
- Ensure controller port (6653) is accessible

### Mininet Issues

**Issue:** Port already in use or cleanup needed

**Solution:**
```bash
sudo mn -c  # Clean up Mininet
pkill -f ryu-manager  # Kill lingering Ryu processes
```

## 📚 Additional Resources

- [Ryu Documentation](https://ryu.readthedocs.io/)
- [OpenFlow Specification](https://www.opennetworking.org/sdn-resources/onf-specifications/openflow)
- [Mininet Project](http://mininet.org/)
- [Open vSwitch Documentation](https://www.openvswitch.org/)

## 📖 Project Documentation

- [Ryu Controller.md](Ryu%20Controller.md): Detailed Ryu setup and configuration
- [Switch Configuration.md](Switch%20Configuration.md): OpenFlow switch setup and configuration
- [Writing the Rules.md](Writing%20the%20Rules.md): Flow rule programming guide





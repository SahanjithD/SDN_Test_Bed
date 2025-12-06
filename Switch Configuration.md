
| **Component**      | **Role**                  | **IP Address (Static)**    | **Key Status**                                   |
| ------------------ | ------------------------- | -------------------------- | ------------------------------------------------ |
| **Linux VM**       | OpenFlow Controller       | $\mathbf{192.168.10.2/24}$ | Bridged Adapter, Firewall Disabled               |
| **Raspberry Pi 4** | OVS Switch ($\text{br0}$) | $\mathbf{192.168.10.3/24}$ | Physical $\text{eth0}$ connected to $\text{br0}$ |




## Configuring A Switch


### Install OVS and dependencies

```
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential libssl-dev libelf-dev python3 python3-pip git \
                   linux-headers-$(uname -r) \
                   openvswitch-switch openvswitch-common
```



## Connections

![[Pasted image 20251021225518.png]]

### On Pi
Verify the Pi sees the USB adapter:

```
lsusb
ip link 
``` 


### Setting up bridge and ports of the SDN switch


Connected laptop and RPI through RJ45 cable

after that OVS bridge was created to serve as the central switch entity.

```
sudo ovs-vsctl add-br br0
```


then port $\text{eth0}$ was connected to the bridge. this port will be responsible for the communication between the controller and the switch

```
sudo ovs-vsctl add-port br0 eth0
```


Assign IP to the bridge for communication ^e9c17a

```
sudo ip a add 192.168.10.3/24 dev br0
```

Bring the bridge interface UP

```
sudo ip link set br0 up
```

Set the OpenFlow Controller target(OpenFlow protocol uses 6653 as the default port)

```
sudo ovs-vsctl set-controller br0 tcp:192.168.10.2:6653
  ```

![[Pasted image 20251021230724.png]]


### Bridge Configuration & Stability


To ensure network stability, proper identification in the controller, and fallback connectivity, the following configurations were applied to the bridge: 

1. **Enable RSTP:** Prevents switching loops. 

2. **Set Datapath ID:** Manually assigns a specific ID (`0000000000000002`) to the switch so it can be clearly identified and numbered in the Ryu Flow Manager UI. 

3. **Set Fail Mode:** Setting this to `standalone` ensures the switch can act as a regular MAC-learning switch if the controller connection fails (though `secure` is often used for pure SDN, `standalone` helped establish initial connectivity).


```bash 
sudo ovs-vsctl set bridge br0 rstp_enable=true 
sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000002 sudo ovs-vsctl set-fail-mode br0 standalone
```



After applying these features, the bridge connected to the Ryu controller successfully. We verified this by achieving **0% packet loss** during pings, and the switch was clearly identified with the correct numbering in the Flow Manager UI.



**All Commands**

```bash
# 1. Create the OVS Bridge
sudo ovs-vsctl add-br br0

# 2. Add the Physical Interface (eth0) to the Bridge
sudo ovs-vsctl add-port br0 eth0
sudo ovs-vsctl add-port br0 eth1
sudo ovs-vsctl add-port br0 eth2

# 3. Assign Static IP to the Bridge (Management Interface)
sudo ip addr add 192.168.10.3/24 dev br0
sudo ip link set br0 up

# 4. Set the Controller Target (Laptop VM IP)
sudo ovs-vsctl set-controller br0 tcp:192.168.10.2:6653

# 5. Enable RSTP (Prevents Loops)
sudo ovs-vsctl set bridge br0 rstp_enable=true

# 6. Set Datapath ID (Unique ID for Controller)
sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000001

# 7. Set Fail Mode (Standalone for connectivity safety, Secure for pure SDN)
sudo ovs-vsctl set-fail-mode br0 standalone
```


verify

```bash
#Verify RSTP (Loop Prevention)
sudo ovs-vsctl get bridge br0 rstp_enable
#### Verify Datapath ID
sudo ovs-vsctl get bridge br0 other-config:datapath-id
#Verify Fail Mode
sudo ovs-vsctl get-fail-mode br0
#Verify Controller Connection Status
sudo ovs-vsctl get controller br0 is_connected
```

after making a change

```bash
#Restart the OVS service to force the change:
sudo /etc/init.d/openvswitch-switch restart
```




###  Controller Setup

A Mint-Linux machine serves as the controller set up on Oracal VM

Adapter settings
![[Pasted image 20251021231815.png]]

A static IP was manually assigned to `enp0s3` and brought it up

```
sudo ip addr add 192.168.10.2/24 dev enp0s3
sudo ip link set enp0s3 up
```

this has to be in the same network as the RPI (`192.168.10.3)

![[Pasted image 20251021232450.png]]
this will be reset after rebooting, can be **made** permanent by editing 
`/etc/netplan/01-network-manager-all.yaml`


### On windows host

Assign static IPs
`Control Panel → Network and Internet → Advanced Network settings → Ethernet → View Additional properties 


```
IP address: 192.168.10.1
Subnet mask: 255.255.255.0
Default gateway: (leave blank)
DNS server: (leave blank)
```

again all 3 IPs have to be in the same network `192.168.10.xx`

(Previously DHCP server was not assigning IPs to the ethernet so It didn't have an IPv4. This caused the ping to fail from host to guest and vise versa)


### verifying

![[Pasted image 20251021234906.png]]

![[Pasted image 20251021235028.png]]

VM can be pinged from the PI and vise versa


Next step : [[Ryu Controller]]







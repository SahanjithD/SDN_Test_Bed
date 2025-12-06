	  
|**Component**|**Required Version**|**Purpose**|
|---|---|---|
|**Python**|**3.9** (Installed via PPA/`apt`)|Bypasses core Python 3.12 incompatibility issues with `eventlet` and `ssl`.|
|**Ryu Controller**|**4.34** (Installed via `pip`)|Known stable version to minimize build errors.|
|**eventlet**|**0.30.2**|Downgraded version to restore the `ALREADY_HANDLED` constant required by Ryu's `wsgi.py`.|
|**dnspython**|**1.16.0**|Specific version to avoid internal conflicts within the `eventlet` dependency chain.|

- **Platform:** Oracle VM VirtualBox
- **Operating System:** Linux Mint
- **Python Version:** 3.9
- **Purpose:** Setting up a working Ryu SDN controller environment compatible with OpenFlow switches.

### Installed Python 3.9 and venv

Linux Mint’s default Python version (3.12) caused compatibility issues with Ryu, so Python 3.9 was manually installed and used for creating a virtual environment.

```
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.9 python3.9-venv -y
```

### Created and Activated a Virtual Environment


```
python3.9 -m venv ryu_venv
source ryu_venv/bin/activate
```

### Fixed Compatibility Issue with Ryu Installation

Initially, installing **Ryu 4.34** failed due to a missing `easy_install` attribute in the latest versions of `setuptools`.  
This happens because **Ryu 4.34 is an older release (from 2021)** that still depends on the old packaging interface removed in modern `setuptools`.

To fix it, `setuptools` was downgraded to a compatible version (`58.0.4`), and `wheel` was installed for smooth package builds.

```
pip install --upgrade pip
pip install setuptools==58.0.4
pip install wheelch
```


### Install Compatible Ryu and Dependencies

After downgrading setuptools, Ryu and its compatible dependency versions were successfully installed.

```
pip install ryu==4.34 eventlet==0.30.2 dnspython==1.16.0
```

### Ran the Ryu Controller

```
ryu-manager ryu.app.simple_switch_13
```

![[Pasted image 20251024111614.png]]

notes

make sure 
- **firewall is disabled** 
	`sudo ip link set br0 up`

- **bridge is up on RPI**
	`sudo ufw disable`

- **verify static IPs on both RPI and VM**
	-if ip has changed [[Switch Configuration#^e9c17a | Assign IP]]	
# Load Balancing Demo

This directory contains a simple Round-Robin Load Balancer application for Ryu and a Mininet topology to test it.

## Files

- `lb_topo.py`: Mininet topology script. Creates a single switch with 1 client (h1) and 3 servers (h2, h3, h4).
- `simple_load_balancer.py`: Ryu application implementing the load balancing logic.

## How to Run

1.  **Start the Ryu Controller:**
    Open a terminal and run the Ryu application.
    ```bash
    ryu-manager applications/SDN_Test_Bed/LoadBalancing/simple_load_balancer.py
    ```

2.  **Start the Mininet Topology:**
    Open another terminal (or split pane) and run the topology script.
    ```bash
    sudo python3 applications/SDN_Test_Bed/LoadBalancing/lb_topo.py
    ```

3.  **Test Load Balancing:**
    In the Mininet CLI, use `ping` from the client (h1) to the Virtual IP (10.0.0.100).
    ```bash
    mininet> h1 ping 10.0.0.100
    ```
    
    You should see successful pings. The Ryu controller logs will show the redirection to different servers (h2, h3, h4) in a round-robin fashion.

    You can also use `tcpdump` on the servers to verify traffic distribution:
    ```bash
    mininet> xterm h2 h3 h4
    # In each xterm window:
    tcpdump -i h2-eth0  # (replace h2 with h3/h4 respectively)
    ```

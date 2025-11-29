
from pox.core import core
import pox.openflow.libopenflow_01 as of
import networkx as nx

from networkx.algorithms.shortest_paths.generic import shortest_path
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr

log = core.getLogger()

def get_networkx_topology_graph():
    """
    get_networkx_topology_graph: nx.Graph

    Returns a NetworkX graph of the current topology formed by the switches
    connected to the controller.
    """
    g = nx.Graph()
    nodes = {l_i.dpid1 for l_i in core.openflow_discovery.adjacency.keys()}
    g.add_nodes_from(nodes)
    for link in core.openflow_discovery.adjacency.keys():
        g.add_edge(link.dpid1, link.dpid2)
    return g 

def get_shortest_path_between(nx_graph, source_dpid, target_dpid):
    """
    get_shortest_path_between: nx.Graph -> int -> int -> List[int]

    Gets the shortest path between <source_node> and <target_node> in
    <nx_graph>. Returns the path as a list of switch DPIDs

    Parameters:
        - nx_graph: A NetworkX graph obtained by calling
          get_networkx_topology_graph.
        - source_dpid: The first DPID in the path.
        - target_dpid: The last DPID in the path.
    """
    return shortest_path(nx_graph, source_dpid, target_dpid)

def get_ports_connecting(source_dpid, target_dpid):
    """
    get_ports_connecting: int -> int -> int

    Returns a tuple containing two port numbers. The first is the port on
    <source_dpid> that connects <source_dpid> to <target_dpid>, the second is
    the port on <target_dpid> that connects <target_dpid> to <source_dpid>. In
    the case that <source_dpid> and <target_dpid> are not _directly_ connected,
    the function returns None.

    Parameters:
        - source_dpid: The DPID of the source node.
        - target_dpid: The DPID of the target node
    """
    links = list(core.openflow_discovery.adjacency.keys())
    print(links)
    the_link = [l_i for l_i in links 
            if l_i.dpid1 == source_dpid
            and l_i.dpid2 == target_dpid]
    if len(the_link) == 0:
        return None
    
    return the_link[0].port1, the_link[0].port2

def get_input_port(path, dpid):
    """
    get_input_port: List[int] -> int -> int

    Given a path, this function returns the port on <dpid> that connects <dpid>
    to the previous hop in the path. Suppose you have the following network
    topology (numbers are port numbers on the switches):

                            2     2  3     2
                          s1 ----- s2 ----- s3
                          |1       |1       | 1
                          |        |        |
                          h1       h2       h3

    And the path is s1 -> s2 -> s3, then calling get_input_port(path, s2) will
    return 2 since the previous hop in the path from s2 is s1 and the port on
    s2 that connects to s1 is 2. Note that if you call get_input_port(path, s1)
    the function will return 1 since it implicitly assumes that the first hop
    in the path is actually the host connected to s1 and the hosts are always
    connected to port 1 of the switch.

    Parameters:
        - path: A list of switch DPIDs representing the path from the source
          dpid to the destination dpid.
        - dpid: A single DPID that is part of the path.
    """
    hop_number = path.index(dpid)
    if hop_number == 0:
        return 1 # The default host port

    local_port, remote_port = \
            get_ports_connecting(path[hop_number - 1], path[hop_number])
    return remote_port

def build_match_for( source_mac
                   , destination_mac
                   , source_ip
                   , destination_ip
                   , source_port
                   , destination_port
                   , in_port):
    """
    build_match_for: str -> str -> str -> str -> int -> int -> int -> ofp_match

    Builds an OpenFlow match structure that matches on the specified inputs,
    when you are implementing install_udp_middlebox_flow you should always use
    this function to build the matches as you are expected to filter on all of
    the criteria specified in this function. The function always creates
    matches that look for UDP packets encapsulated in an IP datagram
    encapslated in an Ethernet frame.

    Parameters:
        - source_mac: A string representing the source MAC address to filter
          on.
        - destination_mac: A string representing the destination MAC address to
          filter on.
        - source_ip: A string representing the source IP address to filter on.
        - destination_ip: A string representing the destination IP address to
          filter on.
        - source_port: An integer representing the source UDP port to filter
          on.
        - destination_port: An integer representing the destination UDP port to
          filter on. 
        - in_port: An integer representing the input switch port to filter on.
    """
    the_match = of.ofp_match()
    the_match.in_port = in_port
    the_match.dl_src = EthAddr(source_mac)
    the_match.dl_dst = EthAddr(destination_mac)
    the_match.dl_type = 0x0800
    the_match.nw_src = IPAddr(source_ip)
    the_match.nw_dst = IPAddr(destination_ip)
    the_match.nw_proto = 17
    the_match.tp_src = source_port
    the_match.tp_dst = destination_port
    return the_match

def build_openflow_flowmod(match, output_port):
    """
    build_openflow_flowmod: ofp_match -> int -> ofp_flowmod
    
    Creates a flowmod that will match on packets specified by <match> and
    output them on <output_port>. Much like build_match_for, you should always
    use this function when creating your Flowmods.

    Paramaters:
        - match: The match specifying the traffic that will match this flow
          rule. Remember that you should always create the match objects using
          the build_match_for function.
        - output_port: The port that matching traffic will be forwarded out of.
    """
    msg = of.ofp_flow_mod()
    msg.match = match
    msg.actions.append(of.ofp_action_output(port=output_port))
    msg.priority = 65534
    return msg

def install_flowmod_on_switch_with_dpid(flowmod, dpid):
    """
    install_flowmod_on_switch_with_dpid: ofp_flowmod -> dpid -> None

    Installs the flowmod on the specified switch. Again, you should be able to
    complete the assignment using only this method to install your flowmods.

    Parameters:
        - flowmod: The flowmod (created with build_openflow_flowmod) to install
          on the switch.
        - dpid: The DPID of the switch to install the flowmod on.
    """
    core.l2_learning.switch_connections[dpid].send(flowmod)

def get_host_entry(dpid):
    """
    get_host_entry: int -> host_tracker.MacEntry

    Gets the host entry for the host connected to the switch with DPID <dpid>.
    To initialize the host entries you need to run pingall from the Mininet
    console! 

    Since we assume that there is only one host connected to each switch this
    method returns the first host entry it finds.

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = [e for e in core.host_tracker.entryByMAC.values()
            if e.dpid == dpid]
    if len(host_entry) == 0:
        raise ValueError("Couldn't find host entry! Did you remember to pingall"
                         " before you started?")
    host_entry = host_entry[0]
    return host_entry

def get_host_ip_from_dpid(dpid):
    """
    get_host_ip_from_dpid: int -> str

    Returns the IP address of the host connected to the switch with DPID <dpid>

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = get_host_entry(dpid)
    return next(iter(host_entry.ipAddrs.keys()))


def get_host_mac_from_dpid(dpid):
    """
    get_host_mac_from_dpid: int -> str

    Returns the MAC address of the host connected to the switch with DPID
    <dpid>.

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = get_host_entry(dpid)
    return host_entry.macaddr

def get_host_port(dpid):
    """
    get_host_port: int -> int

    Returns the port on the switch with DPID <dpid> that connects to the host.
    Remember we always assume that there is exactly one host connected to every
    switch.

    Parameters:
        - dpid: The DPID of the switch.
    """
    host_entry = get_host_entry(dpid)
    return host_entry.port

def install_udp_middlebox_flow( source_dpid
                              , destination_dpid
                              , middlebox_dpid
                              , source_port
                              , destination_port):
    """
    Installs OpenFlow rules to steer UDP traffic from client -> middlebox -> server.
    
    Parameters:
        - source_dpid: DPID of the switch that the client host is attached to
        - destination_dpid: DPID of the switch that the server host is attached to
        - middlebox_dpid: DPID of the switch that the middlebox host is attached to
        - source_port: Source UDP port of the traffic
        - destination_port: Destination UDP port of the traffic
    """
    # Get the network topology graph
    nx_graph = get_networkx_topology_graph()
    
    # Get MAC and IP addresses for client, middlebox, and server hosts
    client_mac = str(get_host_mac_from_dpid(source_dpid))
    client_ip = str(get_host_ip_from_dpid(source_dpid))
    
    middlebox_mac = str(get_host_mac_from_dpid(middlebox_dpid))
    middlebox_ip = str(get_host_ip_from_dpid(middlebox_dpid))
    
    server_mac = str(get_host_mac_from_dpid(destination_dpid))
    server_ip = str(get_host_ip_from_dpid(destination_dpid))
    
    
    # Find shortest path from client switch to middlebox switch
    client_to_middlebox_path = get_shortest_path_between(nx_graph, source_dpid, middlebox_dpid)
    
    # Find shortest path from middlebox switch to server switch
    middlebox_to_server_path = get_shortest_path_between(nx_graph, middlebox_dpid, destination_dpid)
    
    # Find direct path from client to server (to ensure we block it)
    direct_path = get_shortest_path_between(nx_graph, source_dpid, destination_dpid)
    
    # Get all switches that need flow rules
    all_switches_in_path = set(client_to_middlebox_path + middlebox_to_server_path)
    
    # Check if there are switches on direct path not covered by middlebox paths
    direct_path_set = set(direct_path)
    uncovered_switches = direct_path_set - all_switches_in_path
    
    
    for i in range(len(client_to_middlebox_path)):
        current_switch = client_to_middlebox_path[i]
        
        # Determine input port
        in_port = get_input_port(client_to_middlebox_path, current_switch)
        
        # Determine output port
        if i == len(client_to_middlebox_path) - 1:
            # Last switch in path, forward to middlebox host
            out_port = get_host_port(current_switch)
            # Match on client MAC/IP -> server MAC/IP
            # This ensures packets destined for server go to middlebox instead
            match = build_match_for(client_mac, server_mac, client_ip, server_ip,
                                   source_port, destination_port, in_port)
        else:
            # Intermediate switch, forward to next switch in path
            next_switch = client_to_middlebox_path[i + 1]
            local_port, remote_port = get_ports_connecting(current_switch, next_switch)
            out_port = local_port
            # Match on client MAC/IP -> server MAC/IP
            match = build_match_for(client_mac, server_mac, client_ip, server_ip,
                                   source_port, destination_port, in_port)
        
        # Build and install flowmod
        flowmod = build_openflow_flowmod(match, out_port)
        install_flowmod_on_switch_with_dpid(flowmod, current_switch)
    
    # Install flow rules for middlebox -> server path
    # The middlebox forwards packets with original headers (client -> server)
    for i in range(len(middlebox_to_server_path)):
        current_switch = middlebox_to_server_path[i]
        
        # Determine input port
        if i == 0:
            # First switch in path is the middlebox switch, packets come from middlebox host
            in_port = get_host_port(middlebox_dpid)
        else:
            # Intermediate switches, packets come from previous switch
            in_port = get_input_port(middlebox_to_server_path, current_switch)
        
        # Determine output port
        if i == len(middlebox_to_server_path) - 1:
            # Last switch in path, forward to server host
            out_port = get_host_port(current_switch)
            # Match on client MAC/IP -> server MAC/IP (middlebox forwards with original headers)
            match = build_match_for(client_mac, server_mac, client_ip, server_ip,
                                   source_port, destination_port, in_port)
        else:
            # Intermediate switch, forward to next switch in path
            next_switch = middlebox_to_server_path[i + 1]
            local_port, remote_port = get_ports_connecting(current_switch, next_switch)
            out_port = local_port
            # Match on client MAC/IP -> server MAC/IP
            match = build_match_for(client_mac, server_mac, client_ip, server_ip,
                                   source_port, destination_port, in_port)
        
        # Build and install flowmod
        flowmod = build_openflow_flowmod(match, out_port)
        install_flowmod_on_switch_with_dpid(flowmod, current_switch)
    

def do_install():


    source_dpid = None
    destination_dpid = None
    middlebox_dpid = None
    source_port = None
    destination_port = None
    install_udp_middlebox_flow(source_dpid, destination_dpid, middlebox_dpid,
            source_port, destination_port)


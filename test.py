#!/usr/bin/python

"""Topology with 5 switches and 2 hosts
"""

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel

class CSLRTopo( Topo ):

    def __init__( self ):
        "Create Topology"

        # Initialize topology
        Topo.__init__( self )

        # Add hosts
        Alice = self.addHost( 'Alice' )
        Bob = self.addHost( 'Bob' )
        David = self.addHost( 'David' )
        Carol = self.addHost( 'Carol' )

        # Add switches
        s1 = self.addSwitch( 's1', listenPort=4634 )
        s2 = self.addSwitch( 's2', listenPort=4635 )
        s3 = self.addSwitch( 's3', listenPort=4636 )
        r1 = self.addSwitch( 'r1', listenPort=4637 )
        r2 = self.addSwitch( 'r2', listenPort=4638 )

        # Add links between hosts and switches
        self.addLink( Alice, s1 ) # Alice-eth0 <-> s1-eth1
        self.addLink( Bob, s2 ) # Bob-eth0 <-> s2-eth1
        self.addLink( David, s2 ) # David-eth0 <-> s2-eth2
        self.addLink( Carol, s3 ) # Carol-eth0 <-> s3-eth1

        self.addLink( s1, r1, bw=100 ) # s1-eth2 <-> r1-eth1, Bandwidth=100 mbps
        self.addLink( r1, s2, bw=100 ) # r1-eth2 <-> s2-eth3, Bandwidth=100 mbps
        self.addLink( s2, r2, bw=100 ) # s2-eth4 <-> r2-eth1, Bandwidth=100 mbps
        self.addLink( r2, s3, bw=100 ) # r2-eth2 <-> s3-eth2, Bandwidth=100 mbps

def run():
    "Create and configure network"
    topo = CSLRTopo()
    net = Mininet( topo=topo, link=TCLink, controller=None ) 
    
    # Set interface IP and MAC addresses for hosts
    Alice = net.get( 'Alice' )
    Alice.intf( 'Alice-eth0' ).setIP( '10.1.1.17', 24 )
    Alice.intf( 'Alice-eth0' ).setMAC( 'AA:AA:AA:AA:AA:AA' )

    Bob = net.get( 'Bob' )
    Bob.intf( 'Bob-eth0' ).setIP( '10.4.4.48', 24)
    Bob.intf( 'Bob-eth0' ).setMAC( 'B0:B0:B0:B0:B0:B0' )

    Carol = net.get( 'Carol' )
    Carol.intf( 'Carol-eth0' ).setIP( '10.6.6.69', 24 )
    Carol.intf( 'Carol-eth0' ).setMAC( 'CC:CC:CC:CC:CC:CC' )

    David = net.get( 'David' )
    David.intf( 'David-eth0' ).setIP( '10.4.4.96', 24 )
    David.intf( 'David-eth0' ).setMAC( 'D0:D0:D0:D0:D0:D0' )

    # Set interface MAC address for Level 2 switches and interface MAC and IP addresses for Level 3 switches

    s1 = net.get( 's1' )
    s1.intf( 's1-eth1' ).setMAC( '0A:00:01:01:00:01' )
    s1.intf( 's1-eth2' ).setMAC( '0A:00:0A:FE:00:02' )
    
    s2 = net.get( 's2' )
    s2.intf( 's2-eth1' ).setMAC( '0A:00:02:01:00:01' )
    s2.intf( 's2-eth2' ).setMAC( '0A:00:0B:FE:00:02' )
    s2.intf( 's2-eth3' ).setMAC( '0A:00:0D:01:00:03' )
    s2.intf( 's2-eth4' ).setMAC( '0A:00:0C:FE:00:04' )

    s3 = net.get( 's3' )
    s3.intf( 's3-eth1' ).setMAC( '0A:00:03:01:00:01' )
    s3.intf( 's3-eth2' ).setMAC( '0A:00:0D:FE:00:02' )

    r1 = net.get( 'r1' )
    r1.intf( 'r1-eth1' ).setMAC( '0A:00:04:01:00:01' )
    r1.intf( 'r1-eth2' ).setMAC( '0A:00:0E:FE:00:02' )

    r2 = net.get( 'r2' )
    r2.intf( 'r2-eth1' ).setMAC( '0A:00:05:01:00:01' )
    r2.intf( 'r2-eth2' ).setMAC( '0A:00:10:FE:00:02' )


    net.start()

    # Add routing table entries for hosts
    Alice.cmd( 'route add default gw 10.1.1.14 dev Alice-eth0' )
    Bob.cmd( 'route add default gw 10.4.4.14 dev Bob-eth0' )
    Carol.cmd( 'route add default gw 10.6.6.46 dev Carol-eth0' )
    David.cmd( 'route add default gw 10.4.4.28 dev David-eth0' )


    # Add arp cache entries for hosts
    Alice.cmd( 'arp -s 10.1.1.14 0A:00:01:01:00:01 -i Alice-eth0' )
    Bob.cmd( 'arp -s 10.4.4.14 0A:00:02:01:00:01 -i Bob-eth0' )
    Carol.cmd( 'arp -s 10.6.6.46 0A:00:03:01:00:01 -i Carol-eth0' )
    David.cmd( 'arp -s 10.4.4.28 0A:00:0B:FE:00:02 -i David-eth0' )
    Bob.cmd( 'arp -s 10.4.4.96 D0:D0:D0:D0:D0:D0 -i Bob-eth0' )
    David.cmd( 'arp -s 10.4.4.48 B0:B0:B0:B0:B0:B0 -i David-eth0' )
    # Open Mininet Command Line Interface
    CLI(net)

    # Teardown and cleanup
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()

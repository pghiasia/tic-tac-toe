#!/usr/bin/env bash

ovs-vsctl set bridge s1 protocols=OpenFlow13
ovs-vsctl set bridge s2 protocols=OpenFlow13
ovs-vsctl set bridge s3 protocols=OpenFlow13
ovs-vsctl set bridge r1 protocols=OpenFlow13
ovs-vsctl set bridge r2 protocols=OpenFlow13

for switch in s1 s2 s3 r1 r2;
do
    protos=$(ovs-vsctl get bridge $switch protocols)
    echo "Switch $switch supports $protos"
done

ofctl='ovs-ofctl -O OpenFlow13'

# Alice <--> Bob

# Layer-2 switch s1: match only on dl_dst
$ofctl add-flow s1 \
    dl_dst=0A:00:01:01:00:01,actions=mod_dl_src:0A:00:0A:FE:00:02,mod_dl_dst:0A:00:04:01:00:01,output=2

$ofctl add-flow s1 \
    dl_dst=0A:00:0A:FE:00:02,actions=mod_dl_src:0A:00:01:01:00:01,mod_dl_dst:AA:AA:AA:AA:AA:AA,output=1

# Layer-3 switch r1: match only on nw_dst
$ofctl add-flow r1 \
    ip,nw_dst=10.4.4.48,actions=mod_dl_src:0A:00:0E:FE:00:02,mod_dl_dst:0A:00:0D:01:00:03,output=2

$ofctl add-flow r1 \
    ip,nw_dst=10.1.1.17,actions=mod_dl_src:0A:00:04:01:00:01,mod_dl_dst:0A:00:0A:FE:00:02,output=1

$ofctl add-flow s2 \
    dl_dst=0A:00:0D:01:00:03,actions=mod_dl_src:0A:00:02:01:00:01,mod_dl_dst:B0:B0:B0:B0:B0:B0,output=1

$ofctl add-flow s2 \
    dl_dst=0A:00:02:01:00:01,actions=mod_dl_src:0A:00:0D:01:00:03,mod_dl_dst:0A:00:0E:FE:00:02,output=3

# Carol <--> David

$ofctl add-flow s2 \
    dl_dst=0A:00:0B:FE:00:02,actions=mod_dl_src:0A:00:0C:FE:00:04,mod_dl_dst:0A:00:05:01:00:01,output=4

$ofctl add-flow s2 \
    dl_dst=0A:00:0C:FE:00:04,actions=mod_dl_src:0A:00:0B:FE:00:02,mod_dl_dst:D0:D0:D0:D0:D0:D0,output=2

$ofctl add-flow r2 \
    ip,nw_dst=10.6.6.69,actions=mod_dl_src:0A:00:10:FE:00:02,mod_dl_dst:0A:00:0D:FE:00:02,output=2

$ofctl add-flow r2 \
    ip,nw_dst=10.4.4.96,actions=mod_dl_src:0A:00:05:01:00:01,mod_dl_dst:0A:00:0C:FE:00:04,output=1

$ofctl add-flow s3 \
    dl_dst=0A:00:03:01:00:01,actions=mod_dl_src:0A:00:0D:FE:00:02,mod_dl_dst:0A:00:05:01:00:01,output=2

$ofctl add-flow s3 \
    dl_dst=0A:00:0D:FE:00:02,actions=mod_dl_src:0A:00:03:01:00:01,mod_dl_dst:CC:CC:CC:CC:CC:CC,output=1

for switch in s1 s2 s3 r1 r2;
do
    echo "Flows installed $switch:"
    $ofctl dump-flows $switch
    echo ""
done

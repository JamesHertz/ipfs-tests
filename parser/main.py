#! /usr/bin/env python3

from enum import Enum
import sys
import glob
import json
import logging as log
import pandas as pd
import os
import re

from utils import *
from typing import TypedDict
from collections.abc import Generator

# snapshots regular expression
SNAPSHOTS_RE = re.compile('xxx-start-xxx([^"]+?)xxx-end-xxx')

# bucket number and peers_id
Bucket   = list[str]
Snapshot = list[Bucket]

class LookupRecord (TypedDict):
    cid       : str
    time_ms   : float
    providers : list[str]

class NodeInfo(TypedDict):
    pid  : str
    mode : str

class DhtType(Enum):
    SECURE  = 0
    NORMAL  = 1
    DEFAULT = 2

    def parse_from(value):
        if value == 'secure':
            return DhtType.SECURE
        elif value == 'normal':
            return DhtType.NORMAL
        elif value == 'default':
            return DhtType.DEFAULT
        else:
            raise Exception(f'Invalid dht type "{value}"')

def load_cids(filename : str) -> list[str]:
    with open(filename) as file:
        data = file.read()
        aux  = data.split(maxsplit=2)
        return json.loads(aux[-1])

def load_look_up_times(filename : str) -> list[LookupRecord]: #list[dict[str, str]]:
    times = []
    with open(filename) as file:
        for line in file.readlines():
            aux  = line.split(maxsplit=2)
            times.append(json.loads(aux[-1]))
        return times

def load_node_info(filename : str) -> NodeInfo:
    with open(filename) as file:
        return json.loads(file.read())

def load_snapshots(filename : str) -> Generator[Snapshot]:
    with open(filename) as file:
        data = file.read()
        for snap_data in SNAPSHOTS_RE.finditer(data):
            snapshot = []
            info = snap_data.group(1)
            for bucket in info.split('bucket:')[1:]:
                lines = bucket.strip().splitlines()
                snapshot.append([
                    # lines[0] is the bucket number :)
                    line.split(' ', maxsplit=2)[1] for line in lines[1:]
                ])
            yield snapshot


class Node:
    def __init__(self, pid : str, dht_type : DhtType):
        self.pid = pid
        self.dht_type = dht_type

    def get_pid(self) -> str:
        return self.pid

    def get_dht(self) -> DhtType:
        return self.dht_type

# look-ups, snapshots
def parse_files(dirname : str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not os.path.isdir(dirname):
        log.fatal("Error: path %s doesn't exists" % (dirname,))
        sys.exit(1)

    log.info("loading files from: %s", dirname)

    nodes      : dict[str, Node]    = {}
    cids_type  : dict[str, DhtType] = {}
    failed_nodes : set[str] = set()

    # TODO: add loading bar :)
    # loads each node info (which is made of <node-id> and <dht-type> )
    nodes_info = glob.glob('{}/*.info'.format(dirname))
    for info_file in nodes_info:
        info    = load_node_info(info_file)
        peer_id = info['id']
        node    = Node(peer_id, DhtType.parse_from(info['mode']))
        nodes[node.get_pid()] = node

        try:
            cids = load_cids(f'{dirname}/{peer_id}-cids.log')
            for cid in cids:
                cids_type[cid] = node.get_dht()
        except FileNotFoundError:
            # log.warning("Node %s failed during experiment, removing it...", peer_id)
            failed_nodes.add(peer_id)
            del nodes[peer_id]

    records_count = 0 

    # list of (pid, peer_dht, cid, cid_type, lookup_time, provider)
    data = []

    # TODO: add loading bar :)
    # loads all CID records
    for node in nodes.values():
        times = load_look_up_times(f'{dirname}/{node.get_pid()}-lookup-times.log')
        for time_rec in times:
            cid         = time_rec['cid']
            lookup_time = time_rec['time_ms']
            providers   = len(time_rec['providers'])
            c_type      = cids_type.get(cid)

            if c_type == None:
                # TODO: think how to handle this
                # log.warn("Discaring record: %s", time_rec)
                assert providers == 0 
                continue

            assert providers <= 1
            data.append(
                (node.get_pid(), node.get_dht().name, cid,
                    c_type.name, lookup_time, providers)
            )
            records_count += 1
        
    # list of (src_peer, src_dht, dst_peer, dst_dht,  snapshot_nr,  bucket_nr)
    snapshots = []
    for node in nodes.values():
        filename = f'{dirname}/{node.get_pid()}-peers.log'
        for snap_nr , snapshot in enumerate(load_snapshots(filename)):
            for bucket_nr, bucket in enumerate(snapshot):
                for dst_pid in bucket:

                    # TODO: I wonder why?
                    if dst_pid in failed_nodes: continue
                    # assert (dst_pid not in failed_nodes)

                    dst_node = nodes.get(dst_pid)
                    dst_dht = 'Bootstrap' if dst_node is None else nodes[dst_pid].get_dht().name
                    src_dht = node.get_dht()

                    snapshots.append(
                        (node.get_pid(), src_dht.name,  dst_pid, dst_dht, snap_nr, bucket_nr)
                    )


    # TODO: add info about lookups
    log.info("loaded: %d nodes, %d cids, %d look up records", len(nodes), len(cids_type), records_count)
    return pd.DataFrame(data, 
            columns=[PID, PEER_DHT, CID, CID_TYPE, LOOKUP_TIME, PROVIDERS]), pd.DataFrame(snapshots,
                columns=[SRC_PID, SRC_PID, DST_PID, DST_DHT, SNAPSHOT_NR, BUCKET_NR]
            )


# TODO: change this thing :)
def parse_args(args : list[str]) -> list[str]:
    return ['../logs/ipfs-logs' if i == 0 else f'../logs/ipfs-logs-{i:02}' for i in range(6)]
    # return ['../logs/ipfs-logs-04']

def main(args):
    log.basicConfig(level=log.INFO, format="%(levelname)s: %(message)s")

    lookups   = []
    snapshots = []
    for experiment in parse_args(args):
        lkups, snap = parse_files(experiment)
        lookups.append(lkups)
        snapshots.append(snap)

    pd.concat(
        lookups, 
        ignore_index=True
    ).set_index(PID).to_csv('lookups.csv')

    pd.concat(
        snapshots, 
        ignore_index=True
    ).set_index(SRC_PID).to_csv('snapshots.csv')



if __name__ == '__main__':
    main(sys.argv)

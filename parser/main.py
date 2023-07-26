#! /usr/bin/env python3

from enum import Enum
import sys
import glob
import json
import logging as log
import pandas as pd
import os

from utils import *
from typing import TypedDict

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

class Node:
    def __init__(self, pid : str, dht_type : DhtType):
        self.pid = pid
        self.dht_type = dht_type

    def get_pid(self) -> str:
        return self.pid

    def get_dht(self) -> DhtType:
        return self.dht_type

def parse_files(dirname : str) -> pd.DataFrame:
    if not os.path.isdir(dirname):
        log.fatal("Error: path %s doesn't exists" % (dirname,))
        sys.exit(1)

    log.info("loading files from: %s", dirname)

    nodes      : dict[str, Node]    = {}
    cids_type  : dict[str, DhtType] = {}
    data  = []

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
            log.warning("Node %s failed during experiment, removing it...", peer_id)
            del nodes[peer_id]

    records_count = 0 
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
                log.warn("Discaring record: %s", time_rec)
                assert providers == 0 
                continue

            assert providers <= 1
            data.append(
                (node.get_pid(), node.get_dht().name, cid,
                    c_type.name, lookup_time, providers)
            )
            records_count += 1

    log.info("loaded: %d nodes, %d cids, %d look up records", len(nodes), len(cids_type), records_count)
    return pd.DataFrame(data, columns=[PID, PEER_DHT, CID, CID_TYPE, LOOKUP_TIME, PROVIDERS])

def main(args):
    if len(args) < 2:
        print("Error: missing dirname.\nusage: main.py <dirname>")
        sys.exit(1)

    log.basicConfig(level=log.INFO, format="%(levelname)s: %(message)s")
    # TODO: merge all the files in one :)
    res = parse_files(args[1])
    res.set_index(PID).to_csv('data.csv')



if __name__ == '__main__':
    main(sys.argv)

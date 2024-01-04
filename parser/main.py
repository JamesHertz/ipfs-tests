#! /usr/bin/env python3

from enum import Enum
import sys
import glob
import json
import logging as log
import pandas as pd
import os
import re

from utils import Headers as hd
from utils import Lookups as lk
from utils import Snapshots as sp 
from utils import Publishes as pv

from typing import TypedDict
from collections.abc import Iterator

import pprint as pp

# snapshots regular expression
SNAPSHOTS_RE = re.compile('xxx-start-xxx([^"]+?)xxx-end-xxx')

# bucket number and peers_id
Bucket   = list[str]
Snapshot = list[Bucket]

class LookupRecord (TypedDict):
    cid       : str
    time_ms   : float
    type      : str
    providers : list[str]
    queries   : list[str]

class NodeInfo(TypedDict):
    id   : str
    mode : str
    
class PublishRecord(TypedDict):
    cid       : str
    time_ms   : float
    providers : list[str]
    queries   : list[str]    

class ProvideRecord(TypedDict):
    cid       : str
    time_ms   : float
    peers    : list[str]

class FullProvideRecord(PublishRecord):
    store_nodes : list[str]

class DhtType(Enum):
    SECURE  = 0
    NORMAL  = 1
    DEFAULT = 2

    @staticmethod
    def parse_from(value):
        value = value.lower()
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
        return json.loads( data.split(maxsplit=2)[-1] )
        # return [ info['Content'] for info in infos ] #json.loads(aux[-1]) ]

def load_look_up_times(filename : str) -> list[LookupRecord]: #list[dict[str, str]]:
    times = []
    with open(filename) as file:
        for line in file.readlines():
            aux  = line.split(maxsplit=2)[-1]
            times.append(json.loads(aux))
        return times

def load_node_info(filename : str) -> NodeInfo:
    with open(filename) as file:
        return json.loads(file.read())

def load_snapshots(filename : str) -> Iterator[Snapshot]:
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


def load_provides_record(prefix : str) -> list[FullProvideRecord]:
    publish : dict[str, FullProvideRecord] = {}
    with open(f'{prefix}-publish.log') as file:
        for line in file:
            res : PublishRecord = json.loads(
                line.split(' ', maxsplit=2)[-1]
            )
            publish[res['cid']] = res
    # with open(f'{prefix}-provide.log') as file:
    #     for line in file:
    #         res =json.loads(
    #             line.split('\t', maxsplit=4)[-1]
    #         )

    #         # there are some others cids published on the DHT
    #         # when the nodes starts, so I am ignoring them
    #         if res['cid'] in publish:
    #             value = publish[res['cid']]
    #             value['store_nodes'] = res['peers']
            # res : ProvideRecord = json.loads(
            #     line.split(' ', maxsplit=2)[-1]
            # )
    return list(publish.values())

    

    
class Node:
    def __init__(self, pid : str, dht_type : DhtType):
        self.pid = pid
        self.dht_type = dht_type

    def get_pid(self) -> str:
        return self.pid

    def get_dht(self) -> DhtType:
        return self.dht_type

# look-ups, snapshots
def parse_files(dirname : str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not os.path.isdir(dirname):
        log.fatal("Error: path %s doesn't exists" % (dirname,))
        sys.exit(1)

    log.info("loading files from: %s", dirname)

    # TODO: make this instance variables and split the code into methods
    nodes        : dict[str, Node]    = {}
    cids_type    : dict[str, DhtType] = {}
    failed_nodes : set[str] = set()
    useless_cids : set[str] = set()


    resolved = set()
    published = set()

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

        
    # TODO: 
    #  - add test that the provider is right and the type as well

    # list of (src_peer, src_dht, dst_peer, dst_dht,  snapshot_nr,  bucket_nr)
    snapshots = []
    for node in nodes.values():
        filename = f'{dirname}/{node.get_pid()}-peers.log'
        for snap_nr , snapshot in enumerate(load_snapshots(filename)):
            for bucket_nr, bucket in enumerate(snapshot):
                for dst_pid in bucket:

                    # TODO: I wonder why?
                    if dst_pid in failed_nodes: continue

                    dst_dht = nodes[dst_pid].get_dht().name
                    src_dht = node.get_dht()
                    snapshots.append(
                        (node.get_pid(), src_dht.name,  dst_pid, dst_dht, snap_nr, bucket_nr)
                    )
                
    storages = set()
    # list of (cid, src_pid, src_dht, queries_nr, time_ms, storage_node, storage_dht)
    publishes = []
    for node in nodes.values():
        pb_records  = load_provides_record(f'{dirname}/{node.get_pid()}')
        # print(f'node: {node.get_pid()}, dht: {node.get_dht().name}')
        # pp.pprint(pb_records)
        for rec in pb_records:
            published.add(rec['cid'])
            # provs_info[]
            store_nodes = rec.get('store_nodes')
            if len(store_nodes) == 0:
                useless_cids.add(rec['cid'])
                publishes.append((
                    rec['cid'], 
                    node.get_pid(), 
                    node.get_dht().name, 
                    len(rec['queries']), 
                    rec['time_ms'],
                    None, None
                ))
            else:
                for peer in rec['store_nodes']:
                    # my fault, I need to look a this
                    publishes.append((
                        rec['cid'], 
                        node.get_pid(), 
                        node.get_dht().name, 
                        len(rec['queries']), 
                        rec['time_ms'],
                        peer_id, 
                        nodes[peer].get_dht().name
                    ))
                    storages.add(peer)
                # if store_count == 0:
                #     print(f'node: {node.get_pid()}, dht: {node.get_dht().name}')
                #     print(store_count)
                #     print('bootstraps')
                #     pp.pprint(bootstraps)
                #     print('record:')
                #     pp.pprint(rec)
                # assert store_count > 0 , 'you gotta do something'
                # print(store_count)
        # assert store_count == 0 or store_count == len(pb_records), 'something is quite wrong'


    # list of (pid, peer_dht, cid, cid_type, lookup_time, providers, queries)
    lookups = []
    # TODO: add loading bar :)
    # loads all CID records
    for node in nodes.values():
        times = load_look_up_times(f'{dirname}/{node.get_pid()}-lookup-times.log')
        for time_rec in times:
            cid         = time_rec['cid']
            lookup_time = time_rec['time_ms']
            providers   = len(time_rec['providers'])
            c_type      = cids_type.get(cid)
            queries     = len(time_rec['queries'])
            # cid_type    = time_rec['type']
            resolved.add(cid)

            # the node that was supposed to publish this CID failed
            if c_type == None:
                # TODO: think how to handle this
                # log.warn("Discaring record: %s", time_rec)
                assert providers == 0 
                continue

            # Normal node CID that was published only on bootstrap nodes
            # which means it cannot be resolved so its useless
            # if cid in useless_cids: # TODO: discuss this with J. Leitao
            #     # log.warn("Discaring useless CID record: %s", time_rec)
            #     continue


            if c_type != DhtType.DEFAULT:
                aux = time_rec['type']
                assert aux == '' or c_type == DhtType.parse_from(aux), 'cid type mistaken'

            assert providers <= 1
            lookups.append(
                (node.get_pid(), node.get_dht().name, cid,
                    c_type.name, lookup_time, providers, queries)
            )

    # usesless_counts = {}
    # for cid in useless_cids:
    #     c_type = cids_type[cid]
    #     count = usesless_counts.get(c_type, 0)
    #     usesless_counts[c_type] = count + 1

    # print(usesless_counts)
    # TODO: add info about lookups
    log.info("loaded: %d nodes, %d cids, %d look up records, %d snapshot records, %d publish records, %d failed nodes, %d useless cids", len(nodes), len(cids_type), len(lookups), len(snapshots), len(publishes), len(failed_nodes), len(useless_cids))
    return pd.DataFrame(lookups, 
            columns=[lk.PID, lk.PEER_DHT, lk.CID, lk.CID_TYPE, lk.LOOKUP_TIME, lk.PROVIDERS, lk.QUERIES]
           ), pd.DataFrame(snapshots,
               columns=[sp.SRC_PID, sp.SRC_DHT, sp.DST_PID, sp.DST_DHT, sp.SNAPSHOT_NR, sp.BUCKET_NR]
           ), pd.DataFrame(publishes,
                columns=[pv.CID, pv.SRC_PID, pv.SRC_DHT, pv.QUERIES_NR, pv.DURATION, pv.STORAGE_NODE, pv.STORAGE_DHT]
           )


# TODO: change this thing :)
# def parse_args(args : list[str]) -> list[str]:
#     # return ['../logs/ipfs-logs', '../logs/ipfs-logs-2', '../logs/ipfs-logs-3']
#     # return ['../logs/ipfs-logs' if i == 0 else f'../logs/ipfs-logs-{i}' for i in range(6) ]
#     # return [ '../logs/ipfs-logs-12', '../logs/ipfs-logs-13' ]
#     # return [ '../logs/ipfs-logs-22', '../logs/ipfs-logs-24' ]
#     # return [ '../logs/ipfs-logs-25', '../logs/ipfs-logs-26' ]
#     # return [f'../logs/ipfs-logs-{i}' for i in range(33, 39) ]
#     return []

def main(args : list[str]):

    if len(args) < 2:
        print("Error no file provided")
        print(f"usage: {args[0]} directory...")
        sys.exit(1)

    # files = parse_files(args[1:])
    files = args[1:]

    log.basicConfig(level=log.INFO, format="%(levelname)s: %(message)s")

    lookups   = []
    snapshots = []
    publishes = []
    for exp_id, experiment in enumerate(files):
        lkups, snap, psh= parse_files(experiment)

        # set up experiment ids
        lkups[hd.EXP_ID] = exp_id 
        snap[hd.EXP_ID]  = exp_id
        psh[hd.EXP_ID]   = exp_id

        # ...
        lookups.append(lkups)
        snapshots.append(snap)
        publishes.append(psh)

    pd.concat(
        lookups, 
        ignore_index=True
    ).set_index(lk.PID).to_csv('lookups.csv')


    pd.concat(
        snapshots, 
        ignore_index=True
    ).set_index(sp.SRC_PID).to_csv('snapshots.csv')

    pd.concat(
        publishes, 
        ignore_index=True
    ).set_index(pv.SRC_PID).to_csv('publishes.csv')


if __name__ == '__main__':
    main(sys.argv)

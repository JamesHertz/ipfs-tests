#! /usr/bin/env python3

from enum import Enum
import sys
import glob
import json
import logging as log

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
    @classmethod
    def values(cls) -> list['DhtType']:
        return list(map(lambda c: c, cls))


class RTSnapshot:
    def __init__(self, time : int, nodes : list['Peer']):
        self.time  = time
        self.nodes = nodes

class CidRecord:
    def __init__(self, cid : str, type : DhtType):
        self.cid  = cid
        self.type = type

    def __str__(self):
        return '({},{})'.format(self.cid, self.type)

class LookUpRecord:
    def __init__(self, cid_rec : CidRecord , time : int, provs_count : int):
        self.cid_rec     = cid_rec
        self.time        = time
        self.provs_count = provs_count

    def __str__(self):
        return '[cid_rec: {} ; time: {}, providers: {}]'.format(self.cid_rec, self.time, self.providers)

class Peer:
    def __init__(self, pid : str , type : DhtType ):
        self.pid   = pid 
        self.type  = type 
        self.cids      : list[str] = []
        self.snapshots : list[RTSnapshot] = []
        self.look_ups  : list[LookUpRecord] = []
    
    def get_pid(self) -> str :
        return self.pid

    def get_type(self) -> DhtType:
        return self.type

    def get_cids(self) -> list[str]:
        self.cids[:]

    def get_rt_snapshots(self) -> list[str]:
        self.snapshots[:]

    def get_look_up_times(self) -> list[LookUpRecord]:
        return self.look_ups[:]

    def add_cids(self, cids : list[str] ):
        self.cids += cids

    def add_lookup_record(self, cid_rec: CidRecord, time : int, provs_count : int):
        # FIXME: better use map
        self.look_ups.append(LookUpRecord(cid_rec, time, provs_count))

    def add_rt_snapshot(self, time : int, nodes : list['Peer']):
        self.snapshots.append(RTSnapshot(time, nodes))



def load_cids(filename : str) -> list[str]:
    with open(filename) as file:
        data = file.read()
        aux  = data.split(maxsplit=2)
        return json.loads(aux[-1])

def load_look_up_times(filename : str) -> list[dict[str, str]]:
    times = []
    with open(filename) as file:
        for line in file.readlines():
            aux  = line.split(maxsplit=2)
            times.append(json.loads(aux[-1]))
        return times

class Values:
    def __init__(self):
        self.count        = 0
        self.resoved      = 0
        self.total_time   = 0
        self.total_res_time   = 0
        self.total = set()

    def update(self, rec : LookUpRecord):
        self.count      += 1
        self.total_time += rec.time
        if rec.provs_count > 0:
            self.resoved += 1
            self.total_res_time += rec.time
        self.total.add(rec.cid_rec.cid)
        
    def get_resolved(self) -> int:
        return self.resoved

    def get_res_time(self) -> int:
        return 0 if self.resoved == 0 else  self.total_res_time / self.resoved

    def get_non_res_time(self) -> int:
        aux = self.count - self.resoved
        return 0 if aux == 0 else self.total_time - self.total_res_time / aux
    
    def get_time(self) -> int:
        return 0 if self.count == 0 else self.total_time / self.count

    def get_total(self):
        return len(self.total)
    
    def __str__(self):
        return f'''
total cids                     : {self.get_total()}
total resolves                 : {self.count}
total succesful resolves       : {self.get_resolved()}
avg resolve time               : {self.get_time() / 1000} s
avg successfull resolve time   : {self.get_res_time() / 1000} s
avg unsuccessfull resolve time : {self.get_non_res_time() / 1000} s
'''


class ExperimentManager:
    def __init__(self, dirname : str):
        self.records : dict[str, CidRecord] = {}
        self.nodes   : dict[str, 'Peer'] = {}
        self.load_values(dirname)

    def load_values(self, dirname : str):
        log.info("loading values from: %s", dirname)

        # load nodes
        nodes = glob.glob('{}/*.info'.format(dirname))
        for node in nodes:
            with open(node) as file:
                data    = json.loads(file.read())
                peer_id = data['id']
                peer    = Peer(peer_id, DhtType.parse_from(data['mode']))
                self.nodes[peer.get_pid()] = peer
                try:
                    cids = load_cids(f'{dirname}/{peer_id}-cids.log')
                    peer.add_cids(cids)
                    for cid in cids:
                        self.records[cid] = CidRecord(cid, peer.get_type())
                except FileNotFoundError as e:
                    log.warn("Node %s failed during experiment, removing it...", peer_id)
                    del self.nodes[peer_id]
        
        count    = 0
        for peer_id in self.nodes:
            # loads look up times
            times = load_look_up_times(f'{dirname}/{peer_id}-lookup-times.log')
            peer = self.nodes[peer_id]
            count += len(times)
            for time_rec in times:
                cid = time_rec['cid']
                if not cid in self.records:
                    # TODO: think how to handle this
                    log.warn("Discaring record: %s", time_rec)
                    assert len(time_rec['providers']) == 0 
                    continue
                cid_rec = self.records[cid]
                time    = time_rec['time_ms']
                provs   = time_rec['providers']
                assert len(provs) <= 1
                peer.add_lookup_record(cid_rec, time, len(provs))


        log.info("loaded: %d nodes, %d cids, %d look up records", len(self.nodes), len(self.records), count)

    def plot_results(self):
        types = [Values() for x in DhtType.values()]
        all   = Values()

        for node in self.nodes.values():
            idx = node.type.value
            for rec in node.get_look_up_times():
                all.update(rec)
                # TODO: trick paper reader :)
                aux = rec.cid_rec.type.value
                if aux == idx:
                    types[idx].update(rec)

        print()
        for i, value in enumerate(DhtType.values()):
            res = types[i]
            print("%s records " % (value.name,))
            print("---------------------")
            print(res)

        print("all records")
        print("---------------------")
        print(all)
        



def main(args):
    if len(args) < 2:
        print("Error: missing dirname.\nusage: main.py <dirname>")
        sys.exit(1)
    log.basicConfig(level=log.INFO, format="%(levelname)s: %(message)s")
    ex = ExperimentManager(args[1])
    ex.plot_results()



if __name__ == '__main__':
    main(sys.argv)
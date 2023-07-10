from enum import Enum

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


class RTSnapshot:
    def __init__(self, time : int, nodes : list[Peer]):
        self.time  = time
        self.nodes = nodes

class CidRecord:
    def __init__(self, cid : str, type : DhtType):
        self.cid  = cid
        self.type = type

class LookUpRecord:
    def __init__(self, cid_rec : CidRecord , time : int, providers : list[Peer]):
        self.cid_rec   = cid_rec
        self.time      = time
        self.providers = providers

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
        self.look_ups[:]

    def add_cids(self, cids : list[str] ):
        self.cids += cids

    def add_lookup_record(self, cid_rec, time, providers):
        # FIXME: better use map
        self.look_ups.append(LookUpRecord(cid_rec, time, providers))

    def add_rt_snapshot(self, time : int, nodes : list[Peer]):
        self.snapshots.append(RTSnapshot(time, nodes))


class ExperimentManager:
    def __init__(self, dirname : str):
        self.records : dict[str, CidRecord] = {}
        self.nodes   : dict[str, Peer] = {}
        self.load_values(dirname)

    def load_values(self, dirname : str):
        pass





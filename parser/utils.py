# headers of generated csv
class Headers:
    EXP_ID = 'exp-id'

class Lookups(Headers):
    PID         = 'pid'
    PEER_DHT    = 'peer-dht'
    CID         = 'cid'
    CID_TYPE    = 'cid-type'
    LOOKUP_TIME = 'lookup-time (ms)'
    PROVIDERS   = 'providers-nr'

class Snapshots(Headers):
    SRC_PID     = 'src-pid'
    SRC_DHT     = 'src-dht'
    DST_PID     = 'dst-pid'
    DST_DHT     = 'dst-dht'
    BUCKET_NR   = 'bucket-nr'
    SNAPSHOT_NR = 'snapshot-nr'
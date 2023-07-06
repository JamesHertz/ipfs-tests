#!/usr/bin/env bash 

set -e 
export NODE_SEQ_NUM=REPLICA_ID

function main(){
    cp -r "$EXP_REPOS_DIR/ipfs-$NODE_SEQ_NUM" ~/.ipfs
    ipfs bootstrap && root-client

    sleep $((EXP_DURATION*60+600))
}

main $*
#!/usr/bin/env bash 

set -e 
export NODE_SEQ_NUM=$((REPLICA_ID-1))

function main(){
    cp -r "$EXP_REPOS_DIR/repo-$NODE_SEQ_NUM" ~/.ipfs
    ipfs bootstrap && boot-client

    sleep $((EXP_DURATION*60+600))
}

main $*
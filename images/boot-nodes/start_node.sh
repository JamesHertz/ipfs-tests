#!/usr/bin/env bash 

set -e 

source ipfs-config.sh

export REPO_ID=$((REPLICA_ID-1))

function main(){

    # copies and configures the repo
    setup-ipfs-repo

    # start daemon
    ipfs daemon &

    # start the client (that will ouput its address in a file)
    sleep 15 && boot-client

    local wait_time=$((EXP_DURATION*60+600))
    echo "SLEEPING for $wait_time seconds which are $((aux/60)) minutes"
    # wait till the end of the experiment
    sleep "$wait_time"
}

main $*
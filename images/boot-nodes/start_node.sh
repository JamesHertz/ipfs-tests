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

    aux=$((EXP_DURATION*60+600))
    echo "SLEEPING for $aux seconds which are $((aux/60)) minutes"
    # wait till the end of the experiment
    sleep 100000000000

    # sleep $((EXP_DURATION*60+600))
}

main $*
#!/usr/bin/env bash 

set -e

function log(){
    echo -e "\n$1\n------------------------------"
}

function save_logs(){
    # FIXME: find a better solution
    for file in ${LOG_DIR}/* ; do 
        mv "$file" "$SHARED_DIR/$NODE_ID-$(basename "$file")"
    done
}

# others useful enviroment variables
export LOG_DIR=~/log
DIRS="$LOG_DIR $SHARED_DIR"


function main(){

    trap 'save_logs' ERR

    mkdir -p $DIRS

    log "Initializing node..."
    #  TODO: choose a repo based on NODE_SEQ_NUM

    # cp -r ~/.ipfs $BASE_REPO
    tc qdisc add dev eth0 root netem delay 50ms 20ms distribution normal

    NODE_ID=$(ipfs id --format='<id>')

    log "Starting experiments..."

    echo -e "\n-- RUNNNING TRY: $i --\n"

    # start daemon
    ipfs daemon >> "$LOG_DIR/default.log" 2>&1 &

    echo "{\"id\": \"$NODE_ID\", \"mode\": \"$MODE\"}" >> "$SHARED_DIR/$NODE_ID.info"

    # wait a bit
    sleep 15 && ./ipfs-client --mode=$MODE >> "$LOG_DIR/client.log" 2>&1

    log "Killing daemon..."

    # kills ipfs daemon proccess
    kill $(ps | grep ipfs | awk '{print $1}')

    save_logs
}

main $*
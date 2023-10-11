#!/usr/bin/env bash 

set -e

source ipfs-config.sh

function log(){
    echo -e "\n$1\n------------------------------"
}

function save_logs(){
    # FIXME: find a better solution
    for file in ${LOG_DIR}/* ; do 
        echo "copying: $file to $EXP_LOG_DIR/$NODE_ID-$(basename "$file")"
        mv "$file" "$EXP_LOG_DIR/$NODE_ID-$(basename "$file")"
    done
}

function calc_seq_num(){
    local total=$((REPLICA_ID-1))
    if [ "$MODE" = "secure" ] ; then
        total=$((total+EXP_TOTAL_NODES/2))
    fi
    # case $MODE in
    #     default)
    #     ;;
    #     normal)
    #         total=$((2*total))
    #     ;;
    #     secure)
    #         total=$((2*total+1))
    #     ;;
    # esac

    echo $total
}

# others useful enviroment variables
export LOG_DIR=~/log
export NODE_SEQ_NUM=$(calc_seq_num)
export REPO_ID=$((NODE_SEQ_NUM + EXP_BOOT_NODES))
DIRS="$LOG_DIR $SHARED_DIR"
# TODO: NODE_PREFFIX="node-$REPO_ID-$MODE"

function main(){

    trap 'save_logs' ERR

    mkdir -p $DIRS

    log "Initializing node..."

    #  chooses a repo based on NODE_SEQ_NUM
    setup-ipfs-repo

    tc qdisc add dev eth0 root netem delay 50ms 20ms distribution normal

    NODE_ID=$(ipfs id --format='<id>')

    log "Starting experiments..."

    # start daemon
    GOLOG_FILE="$LOG_DIR/provide.log" ipfs daemon >> "$LOG_DIR/peers.log" 2>&1 &

    echo "{\"id\": \"$NODE_ID\", \"mode\": \"$MODE\"}" >> "$EXP_LOG_DIR/$NODE_ID.info"

    # wait a bit
    sleep 20 && ./ipfs-client --mode=$MODE >> "$LOG_DIR/client.log" 2>&1

    log "Killing daemon..."

    # kills ipfs daemon proccess
    # kill $(ps | grep ipfs | awk '{print $1}')
    ipfs shutdown # tururu :)

    save_logs
}

main $*
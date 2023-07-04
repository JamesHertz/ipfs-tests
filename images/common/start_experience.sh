#!/usr/bin/env bash 

set -e

function log(){
    echo -e "\n$1\n------------------------------"
}

function exit_error(){
    # FIXME: find a better solution
    for file in ${LOG_DIR}/* ; do 
        mv "$file" "$SHARED_DIR/$NODE_ID-$(basename "$file")"
    done
}

# others useful enviroment variables
export FILES_DIR=~/files
export LOG_DIR=~/log
BASE_REPO=~/.ipfs-old

DIRS="$FILES_DIR $LOG_DIR $SHARED_DIR"


function main(){

    trap 'exit_error' ERR

    log "Generating files..."
    mkdir -p $DIRS

    for ((i=0;i<FILE_NR;i++)) ; do
        dd bs=1M count="$FILE_SIZE" if=/dev/urandom of="$FILES_DIR/file-$i"
    done

    log "Initializing node..."
    # init node
    ipfs init ; ipfs bootstrap rm --all

    log "Setting configurations..."
    # to avoid confusion
    ipfs config Discovery.MDNS.Enabled --bool false 

    cp -r ~/.ipfs $BASE_REPO
    #tc qdisc add dev eth0 root netem delay 50ms 20ms distribution normal

    NODE_ID=$(ipfs id --format='<id>')

    log "Starting experiments..."
    for ((i=0;i<EXP_TIMES;i++)) ;  do

        echo -e "\n-- RUNNNING TRY: $i --\n"

        local ARGS=--mode=$MODE

        if [ $i -eq 0 ] ; then  # first time
            ARGS="$ARGS --init"
        else # in all the others wait for 2 minutes :)
            log "Resetting repo"
            rm -rf ~/.ipfs 
            cp -r "$BASE_REPO" ~/.ipfs/
            sleep 30
        fi

        # start daemon
        ipfs daemon >> "$LOG_DIR/default.log" 2>&1 &

        # wait a bit
        sleep 15 && ./ipfs-client $ARGS >> "$LOG_DIR/client.log" 2>&1

        log "Killing daemon..."
        # kills ipfs daemon proccess
        kill $(ps | grep ipfs | awk '{print $1}')

        if [ $i -eq 0 ] ; then
            # save node info
            echo "{\"id\": \"$NODE_ID\", \"mode\": \"$MODE\"}" >> "$SHARED_DIR/$NODE_ID.info"
            # copy nodes cids to another folder :)
            mv "$LOG_DIR/cids.log" "$SHARED_DIR/$NODE_ID-cids.log"
            cp ~/.ipfs/config "$BASE_REPO" # just so I keep the bootstrap peers
        fi

        log "Removing files..."
        ipfs pin ls | grep recursive | awk '{print $1}' | xargs ipfs pin rm

        for file in ${LOG_DIR}/* ; do
            mv "$file" "$SHARED_DIR/$i-$NODE_ID-$(basename "$file")"
        done

    done
}

main $*
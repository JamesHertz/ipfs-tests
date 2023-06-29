#!/usr/bin/env bash 

set -e

# if SHARED_DIR not set also throw an error
[[ -z "$MODE" ]] && echo "MODE variable not set...." && exit 1

# TODO: complete
export FILES_DIR=~/files
export LOG_DIR=~/log

# SHARED_DIR=/logs (CHECK THIS)
# generate files :)
#mkdir -p "$FILES_DIR" "$LOG_DIR"

mkdir -p "$FILES_DIR" "$LOG_DIR" "$SHARED_DIR"
for ((i=0;i<FILE_NR;i++)) ; do
    dd bs=1M count="$FILE_SIZE" if=/dev/urandom of="$FILES_DIR/file-$i"
done

# init node
ipfs init ; ipfs bootstrap rm --all

# to avoid confusion
ipfs config Discovery.MDNS.Enabled --bool false 

# tc qdisc add dev eth0 root netem delay 50ms 20ms distribution normal

for ((i=0;i<EXP_TIMES;i++)) ;  do

    echo -e "\n-- RUNNNING TRY: $i --\n"

    ARGS=--mode=$MODE

    if [ $i -eq 0 ] ; then  # first time
         ARGS="$ARGS --init"
    else # in all the others wait for 2 minutes :)
        sleep 120
    fi

    # start daemon
    ipfs daemon >> /dev/null 2>&1 &

    # wait a bit
    sleep 30 && ./ipfs-client $ARGS || exit 1

    # TODO: kill ipfs daemon
    NODE_ID=$(ipfs id --format='<id>')
    echo "nodeId: $NODE_ID"

    echo "Killing daemon..."
    # kill ipfs daemon the proccess
    kill $(ps | awk '{print $1, $4}' | grep ipfs | awk '{print $1}')

    for file in ${LOG_DIR}/* ; do
        mv "$file" "$SHARED_DIR/$i-$NODE_ID-$(basename "$file")"
    done

done

echo "{\"id\": \"$NODE_ID\", \"mode\": \"$MODE\"}" >> "$SHARED_DIR/$NODE_ID.info"
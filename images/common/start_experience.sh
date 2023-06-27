#!/usr/bin/env bash 

set -e

[[ -z "$MODE" ]] ; echo "MODE variable not set...." ; exit 1

export FILES_DIR=~/files
export LOG_DIR=~/log

# generate files :)
mkdir -p "$FILES_DIR" "$LOG_DIR"
for ((i=0;i<FILE_NR;i++)) ; do
    dd bs=1M count="$FILE_SIZE" if=/dev/urandom of="$FILES_DIR/file-$i"
done

# init node
ipfs init ; ipfs bootstrap rm --all

# to avoid confusion
ipfs config Discovery.MDNS.Enabled --bool false 

# start daemon
ipfs daemon &

# wait a bit
sleep 10 && ./ipfs-client

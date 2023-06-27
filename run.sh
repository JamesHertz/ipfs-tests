#!/usr/bin/env bash
set -e

NETWORK=ipfs-net
IMAGE=ipfs-node

re='^[0-9]+$'
if [[ $# -lt 1  || ! "$1" =~ $re ]]; then 
    echo "usage: $0 <number-of-nodes>"
    echo -n "ERROR: " 
    [ $# -lt 1 ] && echo "invalid number or args" || echo "invalid number: $1"
    exit 1
fi

# --env VARIABLE value
# try to use env variables and see what's gonna comeout

echo "running $1 nodes :)"
n=$1
for ((i=0;i<n;i++)) ; do 
    docker run --rm -d --network "$NETWORK" "$IMAGE"
    echo "node-$1 running..."
done

read

echo "killing all images"
docker ps -aq | xargs docker rm -f 


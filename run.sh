#!/usr/bin/env bash

NETWORK=ipfs-net
IMAGE=ipfs-node

re='^[0-9]+$'
if [ $# -lt 1 ] ; then 
    echo "usage: $0 <number-of-nodes>"
    exit 1
fi

if ! [[ "$1" =~ $re ]] ; then 
    echo "Error: invalid <number-of-nodes> : $1 - try again"
    exit 1
fi

echo "running $1 nodes :)"
n=$1
for ((i=0;i<n;i++)) ; do 
    docker run --rm -d --network "$NETWORK" "$IMAGE"
    echo "node-$1 running..."
done

read

echo "killing all images"
docker ps -aq | xargs docker rm -f 


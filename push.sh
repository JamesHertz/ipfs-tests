#! /usr/bin/env bash

set -e

# cluster arch

case $1 in
    --build) 
        GOARCH=amd64 ./build.sh --bin
    ;;
esac

scp -r build.sh bin/ images/ dicluster:~/ipfs-tests
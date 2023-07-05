#! /usr/bin/env bash

set -e

# cluster arch
source ./scripts/utils.sh

files="scripts/ images/"
case $1 in
    --build) 
        pushd ./scripts
            GOARCH=amd64 ./build.sh --bin
        popd
        files="$files bin/"
    ;;
esac

scp -r $files dicluster:~/ipfs-tests
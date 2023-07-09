#! /usr/bin/env bash

set -e

files="scripts/ images/ .env .ipfs-env"
case $1 in
    --build) 
        GOARCH=amd64 ./scripts/build.sh --bin
        files="$files bin/"
    ;;
esac

make -s && scp -r $files dicluster:~/ipfs-tests
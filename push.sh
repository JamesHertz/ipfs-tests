#! /usr/bin/env bash

set -e

files="scripts/ docker/ config/ *.mk .env"
case $1 in
    --build) 
        GOARCH=amd64 ./scripts/script.sh build --bin
        files="$files bin/"
    ;;
esac

scp -r $files dicluster:~/ipfs-tests

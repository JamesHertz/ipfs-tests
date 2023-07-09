#! /usr/bin/env bash

set -e

source scripts/utils.sh

REPOS_DIR="$SHARED_DIR/repos"
FILES_DIR="$SHARED_DIR/files"
CID_FILE="$SHARED_DIR/cids.txt"
USAGE="usage: $0 [ --init | --init-files | --init-repos | --help ]"

function create-swarm {
    log "creating swarm..."
    if docker info | grep -q 'Swarm: active'; then
        echo "--> Swarm already exists"
        return 0
    fi

    echo "--> Creating a new swarm"
    docker swarm init
    join_command=$(docker swarm join-token worker | sed -n "3p")
    echo "--> Adding hosts as workers"
    foreach-host "$join_command" -v
}

function setup-nodes-images(){
    log "Building images..."
    ./scripts/build.sh --images
    foreach-host '$HOME/ipfs-tests/scripts/build.sh --images'
}

function ipfs(){
    bin/ipfs-default $*
}

function init-ipfs-repo(){
    ipfs init ; ipfs bootstrap rm --all

    # to avoid confusion
    ipfs config Discovery.MDNS.Enabled --bool false 
    # reduce resource 
    ipfs config Swarm.ConnMgr.LowWater --json 20
    ipfs config Swarm.ConnMgr.HighWater --json 50
}

function gen-cids(){

    # TODO: Either generate the cids by hashing only the files or do 
    #       a python script to take the txt and turn it into json

    log "Generating cids..."

    export IPFS_PATH=/tmp/.ipfs

    ipfs init > /dev/null  \
        || echo "Ipfs repo already exists, let's move on"

    echo -n > "$CID_FILE"

    local filename=/tmp/my-file
    for ((f=0; f < $FILES_NR;f++)) ; do
        local err=$(dd bs=1M count="$FILE_SIZE" if=/dev/random of="$filename" 2>&1 ) \
            || error "$err"
        local cid=$(ipfs add -q --hash-only "$filename" 2>&1) || error "$cid"

        echo "$cid" >> "$CID_FILE"
        echo "* generated cid-$f"
    done

    rm -rf "$IPFS_PATH" # removed ipfs repo :)
    echo -e "Generated $FILES_NR cids\n"
}

function gen-repos(){
    rm -rf $REPOS_DIR && mkdir -p $REPOS_DIR

    log "Generating repos..."
    for ((r=0; r < REPOS_NR; r++)) ; do
        local reponame="$REPOS_DIR/repo-$r"
        echo " * $reponame"
        IPFS_PATH="$reponame" init-ipfs-repo > /dev/null
    done

    echo "generated $REPOS_NR repos"
}

function main(){

    case $1 in 
        --init)
            gen-cids
            gen-repos
        ;;

        --experiment)
            create-swarm
            setup-nodes-images
        ;;

        --swarm)
            create-swarm
        ;;

        --images)
            setup-nodes-images
        ;;

        --init-cids)
            gen-cids
        ;;

        --init-repos)
            gen-repos
        ;;

        --help|'')
            echo "$USAGE"
        ;;
        *)
            echo -e "Unkown option: $1\n$USAGE"
        ;;
    esac
}

main $*
#! /usr/bin/env bash

source utils.sh
REPOS_DIR="$SHARED_FOLDER/repos"
FILES_DIR="$SHARED_FOLDER/files"
USAGE="usage: $0 [ --init | --init-files | --init-repos | --help ]"


function create-swarm {
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
    build-images
    foreach-host 'cd $HOME/ipfs-tests && ./build.sh --images'
}

function ipfs(){
    ../bin/ipfs-default $*
}

function init-ipfs-repo(){
    ipfs init ; ipfs bootstrap rm --all

    # to avoid confusion
    ipfs config Discovery.MDNS.Enabled --bool false 
    # reduce resource 
    ipfs config Swarm.ConnMgr.LowWater --json 20
    ipfs config Swarm.ConnMgr.HighWater --json 50
}

function gen-repos(){
    rm -rf $REPOS_DIR && mkdir -p $REPOS_DIR

    log "Generating files..."
    for ((f=0; f < FILES_NR;f++)) ; do
        local filename="$FILES_DIR/file-$f"
        echo " * $filename"
        local err=$(dd bs=1M count="$FILE_SIZE" if=/dev/random of="$filename" 2>&1) \
            || error "$err"
    done

    echo -e "generated $FILES_NR files\n"
}

function gen-files(){
    rm -rf $FILES_DIR && mkdir -p $FILES_DIR

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
            gen-files
            gen-repos
        ;;

        --init-files)
            gen-files
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

<< EOF 
        --setup)
            log "creating swarm..."
            create-swarm
            log "Building images..."
            setup-nodes-images
        ;;

        --cluster)
            log "Setting up images in nodes..." 
            setup-nodes-images
        ;;
EOF

# load configs from env file and turn then into eviroment variables
set -a
source .env # so as to save those variables in the enviroment
set +a 

# shared dir on the host side
export SHARED_DIR=~/.ipfs-exp

# values used to generated repos and cids
export REPOS_NR=800
export FILES_NR=$((40*REPOS_NR))
# in megabytes
export FILE_SIZE=10

# used for formating
bold=$(tput bold)
normal=$(tput sgr0)

function popd(){
    command popd $@ >> /dev/null 
}

function pushd(){
    command pushd $@ >> /dev/null
}

function log(){
    echo -e "\n$1\n-----------------------"
}

function error(){
    echo -e "ERROR: $1"
    exit 1
}

function foreach-host(){
    local cmd=$1
    local v=

    [ -z "$cmd" ] && return 1
    [ "$2" = -v ] && v=1

    local curr_host=$(hostname)
    for host in `oarprint host`; do
        if [ "$host" != "$curr_host" ] ; then
            echo "> $host"
            local redirect=$( [ $v ] && tty || echo '/dev/null' )
            # I setted term because of an peculiar oarsh problem 
            # with such environment variable
            oarsh "$host" "export TERM=xterm && $cmd" > $redirect
        fi
    done

    return 0
}


# ---------------------------------------------
# Build helper functions and config variables
# ---------------------------------------------

OUTBIN=$PWD/bin

KUBO_REPO=./repos/kubo-ipfs
CLIENT_REPO=./repos/ipfs-client
# BOOT_REPO=./repos/boot-nodes

DEFAULT_KUBO_SUFFIX="default"

# [ <name>:libp2p@version , ... ]
# NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1.2" "normal:v0.21.1-normal-v1")
# NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1.5" "normal:v0.21.1-normal-v1.1")
NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1.6" "normal:v0.21.1-normal-v1.1")

# output binary
KUBO_OUTPUT_BIN=cmd/ipfs/ipfs

# common version for all new new kubo versions
LIBP2P_VERSION=v0.26.4-research
KBUCKET_VERSION=v0.5.1-research-v2.1

# dependecies name
LIBP2P=go-libp2p
KBUCKET=go-libp2p-kbucket
DHT=go-libp2p-kad-dht

# Docker Images 
# ----------------

# ipfs client binary (not an ipfs node)
CLIENT_BIN="ipfs-client"

# docker filel and image name
DOCKER_FILE=./docker/Dockerfile
DOCKER_IMAGE=ipfs-tests

# set up default dependecies
function new-dht-default-depencies(){
    go mod edit -replace "github.com/libp2p/$LIBP2P"="github.com/JamesHertz/$LIBP2P@$LIBP2P_VERSION"
    go mod edit -replace "github.com/libp2p/$KBUCKET"="github.com/JamesHertz/$KBUCKET@$KBUCKET_VERSION"
}

function switch-dht-depency(){
    local new_version=$1
    go mod edit -replace "github.com/libp2p/$DHT"="github.com/JamesHertz/$DHT@$new_version"
}

# -------------------------------------------
# Setup helper functions and config variables
# -------------------------------------------

REPOS_DIR="$SHARED_DIR/repos"
FILES_DIR="$SHARED_DIR/files"
CID_FILE="$SHARED_DIR/cids.txt"

function ipfs(){
    bin/ipfs-default $*
}

# ---------------------------------------------------
# Experiment helper functions and configs variables
# ---------------------------------------------------

# experiment folders and files
export SHARED_LOG_DIR=$SHARED_DIR/$(basename $EXP_LOG_DIR)
export SHARED_BOOT_DIR=$SHARED_DIR/$(basename $EXP_BOOT_DIR)
export BOOT_FILE=$SHARED_BOOT_DIR/$(basename $EXP_BOOT_FILE)
OUT_LOGS=./logs

EXP_DIRS="$SHARED_LOG_DIR $SHARED_BOOT_DIR"

STACK_NAME=ipfs-experiment
# setup values
IPFS_ENV_FILE=.ipfs-env

function create-boot-file(){
    log "Creating boot file..."
    scripts/utils.py build
}


function convert-timestamp(){
    scripts/utils.py convert "$1"
}

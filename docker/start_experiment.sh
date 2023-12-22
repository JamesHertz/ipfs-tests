#!/usr/bin/env bash 

set -e 
shopt -s expand_aliases

# some setup functions
function setup-ipfs-alias(){
    case $NODE_MODE in
        normal)
            alias ipfs=ipfs-normal
        ;;
        secure)
            alias ipfs=ipfs-secure
        ;;
        *)
            alias ipfs=ipfs-default
        ;;
    esac
}

function calc-sequence-number(){
    local total=$((REPLICA_ID-1))
    if [ "$NODE_MODE" = "secure" ] ; then
        total=$((total+EXP_TOTAL_NODES/2))
    fi

    if [ "$NODE_ROLE" != "bootstrap" ] ; then
        local delta=$TOTAL_BOOT_NODES
        case $NODE_MODE in
            normal)
                delta=$EXP_NORMAL_BOOT_NODES
            ;;
            secure)
                delta=$EXP_SECURE_BOOT_NODES
            ;;
        esac
        total=$((total+delta))
    fi

    echo $total
}

# init some variables c:
export LOG_DIR=~/log
export NODE_SEQ_NR=$(calc-sequence-number)
DIRS="$LOG_DIR $SHARED_DIR"
exec 2>&1 > "$LOG_DIR/$NODE_SEQ_NR-bash.log"
setup-ipfs-alias  


# helper functions
function log(){
    echo -e "\n$1\n------------------------------"
}

function error(){
    echo -e "ERROR: $1"
    return 1
}

function save-logs(){

    if [ -z "$NODE_ID" ] ; then
        NODE_ID=${NODE_SEQ_NR}
    fi

    # FIXME: find a better solution
    for file in ${LOG_DIR}/* ; do 
        echo "copying: $file to $EXP_LOG_DIR/$NODE_ID-$(basename "$file")"
        mv "$file" "$EXP_LOG_DIR/$NODE_ID-$(basename "$file")"
    done
}

# config function
function setup-ipfs-repo(){
    # gets the repo
    cp -r "$EXP_REPOS_DIR/repo-$NODE_SEQ_NR" ~/.ipfs

    # to reset the it's addresses
    ipfs config profile apply default-networking 

    # remove bootstraps 
    ipfs bootstrap rm --all

    # to avoid confusion
    ipfs config Discovery.MDNS.Enabled --bool false 

    # reduce resource consuntion
    ipfs config Swarm.ConnMgr.LowWater --json 20
    ipfs config Swarm.ConnMgr.HighWater --json 50

    # grade period
    ipfs config Swarm.ConnMgr.GracePeriod 60s
}

# main function
function main(){

    trap 'save-logs' ERR

    [ -z "$NODE_MODE" ] &&  error "NODE_MODE is not set"
    [ -z "$NODE_ROLE" ] &&  error "NODE_ROLE is not set"

    mkdir -p $DIRS

    log "Initializing node..."

    #  chooses a repo based on NODE_SEQ_NR
    setup-ipfs-repo

    tc qdisc add dev eth0 root netem delay 50ms 20ms distribution normal

    NODE_ID=$(ipfs id --format='<id>')

    log "Starting experiments..."

    # start daemon
    GOLOG_FILE="$LOG_DIR/provide.log" ipfs daemon >> "$LOG_DIR/peers.log" 2>&1 &

    cat > "${EXP_LOG_DIR}/${NODE_ID}.info" << EOF
{"id": "$NODE_ID", "mode": "$NODE_MODE", "role": "$NODE_ROLE"} 
EOF 

    # wait a bit
    ./ipfs-client >> "$LOG_DIR/client.log" 2>&1

    log "Killing daemon..."
    ipfs shutdown 

    save-logs
}

main $*
#!/usr/bin/env bash

set -e 

NETWORK=sipfs-net
# VNAME=ipfs-logs
OUT_LOGS=~/.ipfs-exp/logs
VOLUME="type=bind,source=$OUT_LOGS,target=/logs"
#REPLICAS=2
USAGE="usage: $0 [ --run | --logs | --help | --clean ]"
LOGS_DIR=logs
# TODO: think of something better than this
IPFS_ENV_FILE=.ipfs-env

source utils.sh

function stop-all(){
   docker service ls --format "{{.ID}}" | xargs -r docker service rm
}

function abort(){
   echo "ERROR: aborting all services"
   stop-all
}

function create-network {
  # Check if network already exists
  local net=$(docker network ls --filter name=$NETWORK -q)
  if [ -z "$net" ] ; then
    log "Creating network"
    docker network create --driver overlay \
            --subnet 192.169.0.0/16 $NETWORK
  fi
}

function get-hosts(){
    oarprint host
}
 
function run-services(){

    # clear logs dir

    trap 'abort' ERR
    trap 'abort' SIGINT

    create-network

    log "Setting volumes..."
    [ -d "$OUT_LOGS" ] && rm -rf "$OUT_LOGS"
    mkdir -p "$OUT_LOGS"

    # TODO: 
    #   - setup values for Kbucket size and number of stream
    #   - have the two experiments running :)

    log "Launching master..."
    docker service create --name master --restart-condition=none \
        --hostname webmaster --network "$NETWORK"  webmaster 

    log "Launching ipfs-normal replicas..."
    docker service create --name ipfs-normal --replicas 2 \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" \
        --env-file="$IPFS_ENV_FILE" ipfs-normal

    log "Launching ipfs-secure replicas..."
    docker service create --name ipfs-secure --replicas 2 \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" \
        --env-file="$IPFS_ENV_FILE" ipfs-secure

    echo -e "\nDone!!!\n"
}

function get-logs () {

    log "Stopping services...."
    stop-all

    log "Getting logs..."
    # decide the folder mane where the logs will be putted
    ! [ -d "$LOGS_DIR" ] && mkdir "$LOGS_DIR"

    local count=$(ls "$LOGS_DIR" | wc -l | xargs)

    local dst_log_dir="$LOGS_DIR/ipfs-logs"
    [ $count -gt 0 ] && dst_log_dir="$dst_log_dir-$count"

    cp "$OUT_LOGS" "$dst_log_dir"

    echo -e "\nLogs saved in: $dst_log_dir\n"
}

function main(){
    # reserve nodes: -t docker-swarm
    case $1 in 
        --run|'')
            run-services
        ;;
        --logs)
            get-logs
        ;;
        --clean)
            log "Stopping all the services"
            stop-all
        ;;
        --help)
        echo "$USAGE" 
        ;;
        *)
            echo -e "$USAGE\nError: unknown option: $1"
            exit 1
        ;;
    esac
}

main $*
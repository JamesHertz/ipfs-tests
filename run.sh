#!/usr/bin/env bash

set -e 

NETWORK=sipfs-net
VNAME=ipfs-logs
VOLUME="type=volume,source=$VNAME,target=/logs"
#REPLICAS=2
USAGE="usage: $0 [ --run | --logs | --help | --clean ]"
LOGS_DIR=logs

function log(){
    echo -e "\n$1\n-----------------------"
}

function stop_all(){
   docker service ls --format "{{.ID}}" | xargs docker service rm
}

function abort(){
   echo "ERROR: aborting all services"
   stop_all
}


function run_services(){
    trap 'abort' ERR
    trap 'abort' SIGINT

    log "Setting volumes..."
    docker volume rm "$VNAME" && docker volume create "$VNAME"

    log "Launching master..."
    docker service create --name master --restart-condition=none \
        --hostname webmaster --network "$NETWORK"  webmaster 

    log "Launching ipfs-normal replicas..."
    docker service create --name ipfs-normal --replicas 2 \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" ipfs-normal

    log "Launching ipfs-secure replicas..."
    docker service create --name ipfs-secure --replicas 2 \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" ipfs-secure

    echo -e "\nDone!!!\n"
}

function get_logs () {

    log "Stopping services...."
    stop_all

    log "Getting logs..."
    # decide the folder mane where the logs will be putted
    ! [ -d "$LOGS_DIR" ] && mkdir "$LOGS_DIR"

    local count=$(ls "$LOGS_DIR" | wc -l | xargs)

    local dst_log_dir="$LOGS_DIR/ipfs-logs"
    [ $count -gt 0 ] && dst_log_dir="$dst_log_dir-$count"

    # copy logs from driver
    docker run --rm --name log-collector -d -v "$VNAME:/logs" ubuntu sleep 100000
    docker cp  log-collector:/logs "$dst_log_dir"

    # stop launched container :)
    docker ps -aq | xargs docker rm -f >> /dev/null

    echo -e "\nLogs saved in: $dst_log_dir\n"
}

case $1 in 
    --run|'')
        run_services
    ;;
    --logs)
        get_logs
    ;;
    --clean)
        log "Stopping all the services"
        stop_all
    ;;
    --help)
       echo "$USAGE" 
     ;;
    *)
        echo -e "$USAGE\nError: unknown option: $1"
        exit 1
    ;;
esac

#!/usr/bin/env bash

set -e 

# env file

set -a
source .env # so as to save those variables in the enviroment
set +a 

source scripts/utils.sh

# experiment folders
IPFS_ENV_FILE=.ipfs-env
SHARED_LOG_DIR=$SHARED_DIR/$(basename $LOG_DIR)
SHARED_BOOT_DIR=$SHARED_DIR/$(basename $EXP_BOOT_DIR)
EXP_DIRS="$SHARED_LOG_DIR $SHARED_BOOT_DIR"

# setup values
NETWORK=sipfs-net
VOLUME="type=bind,source=$SHARED_DIR,target=/exp"

# experiments ID
BASE_EXP_ID=base
NEW_EXP_ID=new

# usage
USAGE="usage: $0 <command>

The commands are:
    run ${bold}<id>${normal}  - runs experiment identified by ${bold}<id>${normal} that can be ${bold}${BASE_EXP_ID}${normal} or ${bold}${NEW_EXP_ID}${normal}
    logs      - clear and save logs in the LOG_DIR/ipfs-log-{count} dir
    clean     - clear logs without saving them
    help      - displays the usage 
"


# ---------------------
#   Helping functions
# ---------------------
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
 
# -------------------------
#   Experiments functions
# -------------------------
function base-exp(){
    log "Launching ipfs-default replicas..."
    docker service create --name ipfs-normal --replicas $EXP_TOTAL_NODES \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" \
        --env-file="$IPFS_ENV_FILE" ipfs-normal
}

function new-exp(){

    local half_nodes=$((EXP_TOTAL_NODES/2))

    log "Launching ipfs-normal replicas..."
    docker service create --name ipfs-normal --replicas $half_nodes \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" \
        --env-file="$IPFS_ENV_FILE" ipfs-normal

    log "Launching ipfs-secure replicas..."
    docker service create --name ipfs-secure --replicas $half_nodes \
        --cap-add=NET_ADMIN --mount "$VOLUME" \
        --restart-condition=none --network "$NETWORK" \
        --env-file="$IPFS_ENV_FILE" ipfs-secure
}

# run main function
function run-experiment(){
    # TODO: 
    #    x launch the boot nodes
    #    x wait for them to finish and generate the EXP_BOOT_FILE
    #    - run all the nodes and wait to the experiment to end (should I?)

    local boot_image=
    local experiment=

    case $1 in 
        $BASE_EXP_ID)
            boot_image=upgradable-boot
            experiment=base-exp
        ;;

        $NEW_EXP_ID)
            boot_image=default-boot
            experiment=new-exp
        ;;

        *)
            error "invalid <id> '$2' or not specified, please run '$0 help' to list the usage"
        ;;
    esac


    trap 'abort' ERR
    trap 'abort' SIGINT

    create-network

    log "Setting volumes..."
    rm -rf $EXP_DIRS && mkdir -p $EXP_DIRS

    # log "Launching bootstraps..."
    # docker service create --name boot-nodes --restart-condition=none \
    #     --env-file="$IPFS_ENV_FILE" --network "$NETWORK"  "$boot_image"

    # log "Waiting 2 minutes and Building boot file..."
    # # wait a bit and build boot-file
    # sleep 120 && scripts/boot-file-builder.py

    # $experiment
    # # sleep ((EXP_TIME*60+120)) && get-logs # should I?
    # echo -e "\nDone!!!\n"
}

# function get-logs () {

#     log "Stopping services...."
#     stop-all

#     log "Getting logs..."
#     # decide the folder mane where the logs will be putted
#     ! [ -d "$LOGS_DIR" ] && mkdir "$LOGS_DIR"

#     local count=$(ls "$LOGS_DIR" | wc -l | xargs)

#     local dst_log_dir="$LOGS_DIR/ipfs-logs"
#     [ $count -gt 0 ] && dst_log_dir="$dst_log_dir-$count"

#     cp "$OUT_LOGS" "$dst_log_dir"

#     echo -e "\nLogs saved in: $dst_log_dir\n"
# }

function main(){
    # reserve nodes: -t docker-swarm
    case $1 in 
        run)
            run-experiment "$2"
        ;;
        # logs)
        #     get-logs
        # ;;
        clean)
            log "Stopping all the services"
            stop-all
        ;;
        
        help|'')
            echo "$USAGE" 
        ;;

        *)
            error "unknown command: $1\n\n$USAGE"
        ;;
    esac
}

main $*
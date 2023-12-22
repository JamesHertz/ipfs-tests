#!/usr/bin/env bash

set -e 

# env file
set -a
source .env # so as to save those variables in the enviroment
set +a 

source scripts/utils.sh

# experiment folders and files
export SHARED_LOG_DIR=$SHARED_DIR/$(basename $EXP_LOG_DIR)
export SHARED_BOOT_DIR=$SHARED_DIR/$(basename $EXP_BOOT_DIR)
export BOOT_FILE=$SHARED_BOOT_DIR/$(basename $EXP_BOOT_FILE)
OUT_LOGS=./logs

EXP_DIRS="$SHARED_LOG_DIR $SHARED_BOOT_DIR"

STACK_NAME=ipfs-experiment
# setup values
IPFS_ENV_FILE=.ipfs-env
NETWORK=sipfs-net
VOLUME="type=bind,source=$SHARED_DIR,target=/exp"

# experiments ID
BASE_EXP_ID=base
NEW_EXP_ID=new

# usage
USAGE="usage: $0 <command>

The commands are:
    run ${bold}<compose-file>${normal}  
            runs experiment defined on ${bold}<compose-file>${normal}
    logs    clear and save logs in the ${bold}LOG_DIR/ipfs-log-{${normal}count${bold}}${normal} dir
    clean   clear logs without saving them
    help    displays the usage 
"


# docker config


COMMON_SERV_CFG="--limit-memory=1GB --env-file=$IPFS_ENV_FILE
--restart-condition=none --network $NETWORK --mount $VOLUME"

# ---------------------
#   Helping functions
# ---------------------
function stop-all(){
    docker stack rm "$STACK_NAME"
}

function abort(){
   echo "ERROR: aborting all services"
   stop-all
   exit 1
}


function create-boot-file(){
    log "Creating boot file..."
    scripts/utils.py build
}


function convert-timestamp(){
    scripts/utils.py convert $1
}

# function create-network {
#   # Check if network already exists
#   local net=$(docker network ls --filter name=$NETWORK -q)
#   if [ -z "$net" ] ; then
#     log "Creating network"
#     docker network create --driver overlay --attachable \
#             --subnet 192.169.0.0/16 $NETWORK
#   fi
# }
 
# -------------------------
#   Experiments functions
# -------------------------
# function base-exp(){
#     log "Launching ipfs-default replicas..."
#     docker service create --name ipfs-default --replicas $EXP_TOTAL_NODES \
#         --cap-add=NET_ADMIN $COMMON_SERV_CFG ipfs-default
#         # --cap-add=NET_ADMIN --mount "$VOLUME" \
#         # --restart-condition=none --network "$NETWORK" \
#         # --env-file="$IPFS_ENV_FILE" ipfs-default
# }

# function new-exp(){

#     local half_nodes=$((EXP_TOTAL_NODES/2))

#     log "Launching ipfs-normal replicas..."
#     docker service create --name ipfs-normal --replicas $half_nodes \
#          --cap-add=NET_ADMIN $COMMON_SERV_CFG ipfs-normal
#         # --cap-add=NET_ADMIN --mount "$VOLUME" \
#         # --restart-condition=none --network "$NETWORK" \
#         # --env-file="$IPFS_ENV_FILE" ipfs-normal

#     log "Launching ipfs-secure replicas..."
#     docker service create --name ipfs-secure --replicas $half_nodes \
#         --cap-add=NET_ADMIN $COMMON_SERV_CFG ipfs-secure
#         # --cap-add=NET_ADMIN --mount "$VOLUME" \
#         # --restart-condition=none --network "$NETWORK" \
#         # --env-file="$IPFS_ENV_FILE" ipfs-secure
# }

# run main function
function run-experiment(){
    compose-file=$1
    ![ -f "${compose-file}"] && error "File '${compose-file}' not found"

    make -s

    trap 'abort' ERR
    trap 'abort' SIGINT

    log "Setting volumes..."
    rm -rf $EXP_DIRS && mkdir -p $EXP_DIRS

    #TODO: set start time ....
    local current_time=$(date +%s)
    local launch_seconds=$(convert-timestamp "$EXP_LAUNCH_PERIOD")
    export EXP_START_TIME=$((current_time+launch_seconds))

    log "Starting experiment..."
    docker stack deploy -c "${compose-file}" "$STACK_NAME"

    log "Waiting 1 minutes and Building boot file..."
    # wait a bit and build boot-file
    sleep 60 && build-boot-file

    local duration_seconds=$(convert-timestamp "$EXP_DURATION")
    local current_time=$(date +%s)

    local wait_time=$((current_time-duration_seconds-EXP_START_TIME))
    log "Waiting $((wait_time/60)) minutes to experiment end"

    sleep "$wait_time" && get-logs
    echo -e "\nDone!!!\n"
}

function get-logs () {

    log "Stopping services...."
    stop-all && sleep 60 # sleeping a bit

    log "Getting logs..."
    # decide the folder mane where the logs will be putted
    ! [ -d "$OUT_LOGS" ] && mkdir "$OUT_LOGS"

    local count=$(ls "$OUT_LOGS" | wc -l | xargs)

    local dst_log_dir="$OUT_LOGS/ipfs-logs"
    [ $count -gt 0 ] && dst_log_dir="$dst_log_dir-$count"

    cp -r "$SHARED_LOG_DIR" "$dst_log_dir"

    echo -e "\nLogs saved in: $dst_log_dir\n"
}

function main(){
    # reserve nodes: -t docker-swarm
    case $1 in 
        run)
            run-experiment "$2"
        ;;
        logs)
            get-logs
        ;;
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
#!/usr/bin/env bash

# TODO: research about -E
set -eE

source scripts/utils.sh

# -----------------------
# Build functions
# -----------------------

# receives the name suffix as argument
function build-kubo-bin(){
    local binary_name=$1

    echo -e "> building $binary_name..."

    go mod tidy
    make clean > /dev/null && GOOS='linux' make build 
    cp "$KUBO_OUTPUT_BIN" "$OUTBIN/$binary_name"

    echo
}


function build-binaries(){
    log "building binaries..."
    # if bin doesn't exists generate it :)
    # delete everyting inside outbin
    rm -rf "$OUTBIN" && mkdir -p "$OUTBIN"

    # get the most update version of everything
    log "reseting submodules..."
    git submodule foreach git reset --hard 

    log "updating submodules..."
    git submodule update --remote

    #log "pulling last submodules changes..."
    # git pull --recurse-submodules 

    log "building client binaries"
    # generate ipfs-client and webmaster binaries
    pushd "$CLIENT_REPO"
        if [ -f Makefile ] ; then 
            echo "> building $CLIENT_REPO"  
            make clean > /dev/null && GOOS='linux' make && cp bin/* "$OUTBIN"
        fi
    popd 

    log "building kubo versions"
    # generate the default version 
    pushd "$KUBO_REPO" 
        build-kubo-bin "ipfs-$DEFAULT_KUBO_SUFFIX"

        new-dht-default-depencies

        for version_info in ${NEW_KUBO_VERSIONS[@]}; do

            IFS=':' read -ra values <<< "$version_info"
            if ! [ ${#values[@]} -eq 2 ] ; then
                echo "Invalid version info: $values"
                exit 1
            fi

            local kubo_suffix=${values[0]}
            local dht_version=${values[1]}

            # go mod edit -replace "github.com/libp2p/$DHT"="github.com/JamesHertz/$DHT@$dht_version"
            switch-dht-depency "$dht_version"

            build-kubo-bin "ipfs-$kubo_suffix"
        done

    popd 
}

function build-images(){
    log "building image..."
    docker build -t "$DOCKER_IMAGE" --file "$DOCKER_FILE" . 
}

# -----------------------
# Setup functions
# -----------------------

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
    log "Setting images in nodes"
    ./scripts/script.sh build --images
    foreach-host 'cd $HOME/ipfs-tests && scripts/build.sh --images'
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
        IPFS_PATH="$reponame" ipfs init > /dev/null
    done

    echo "generated $REPOS_NR repos"
}

# -----------------------
# Experiment functions
# -----------------------

function stop-all(){
    docker stack rm "$STACK_NAME"
}

function abort(){
   echo "ERROR: aborting all services"
   stop-all
   exit 1
}

# run main function
function run-experiment(){
    local compose_file=$1
    ! [ -f "$compose_file" ] && error "File '$compose_file' not found\n\n$USAGE"

    make -s

    trap 'abort' ERR
    trap 'abort' SIGINT

    log "Setting volumes..."
    rm -rf $EXP_DIRS && mkdir -p $EXP_DIRS

    #TODO: set start time ....
    local current_time=$(date +%s)
    local launch_seconds=$(convert-timestamp "$EXP_LAUNCH_PERIOD")
    export EXP_START_TIME=$((current_time+launch_seconds))
    echo -e "\nEXP_START_TIME=$EXP_START_TIME" >> "$IPFS_ENV_FILE"

    log "Starting experiment..."
    docker stack deploy -c "$compose_file" "$STACK_NAME"

    log "Waiting 1 minutes and Building boot file..."
    # wait a bit and build boot-file
    sleep 60  && create-boot-file

    local duration_seconds=$(convert-timestamp "$EXP_DURATION")
    local end_time=$((EXP_START_TIME+duration_seconds))

    # recalculate current time c:
    local current_time=$(date +%s)
    local wait_time=$((end_time-current_time))

    log "Waiting until $(date -d @$end_time) to end experiment"

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

# -----------------------
#  Main functions
# -----------------------

# usage
USAGE="usage: $0 <command>

The commands are:
    start ${bold}<compose_file>${normal}  
            runs experiment defined on ${bold}<compose_file>${normal}
    build --images, --bin, --all
            builds docker images, binaries or both
    setup --swarm, --images, --experiment
            creates a swarm, sets images in nodes or both
    init --cids, --repos
            generates cids, repos or both (if no option is given)
    logs    clear and save logs in the ${bold}LOG_DIR/ipfs-log-{${normal}count${bold}}${normal} dir
    clean   clear logs without saving them
    help    displays the usage 
"

function run-build(){
    case $1 in
        --images)
            build-images
        ;;
        --bin)
            build-binaries
        ;;
        --all)
            log "building images and binaries..."
            build-images
            build-binaries
        ;;
        '')
            error "missing build option\n\n$USAGE"
        ;;
        *)
            error "unknown build option: '$1'\n\n$USAGE"
        ;;
    esac
}

function run-setup(){
    case $1 in
        --swarm)
            create-swarm
        ;;
        --images)
            setup-nodes-images
        ;;
        --experiment)
            log "Setting up swarm and images..."
            create-swarm
            setup-nodes-images
        ;;
        '')
            error "missing setup option\n\n$USAGE"
        ;;
        *)
            error "unknown setup option: $1\n\n$USAGE"
        ;;
    esac
}


function run-init(){
    case $1 in
        --cids)
            gen-cids
        ;;
        --repos)
            gen-repos
        ;;
        *)
            log "Generating cids and repos..."
            gen-cids
            gen-repos
        ;;
    esac
}


function main(){
    # reserve nodes: -t docker-swarm
    case $1 in 
        start)
            run-experiment "$2"
        ;;
        build)
            shift && run-build $*
        ;;

        setup)
            shift && run-setup $*
        ;;

        init)
            shift && run-init $*
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
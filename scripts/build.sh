#! /usr/bin/env bash
set -e


# FIXME: ...
source scripts/utils.sh 


# ------------------
#   Binaries
# ------------------

OUTBIN=$PWD/bin

KUBO_REPO=./repos/kubo-ipfs
CLIENT_REPO=./repos/ipfs-client
BOOT_REPO=./repos/boot-nodes

DEFAULT_KUBO_SUFFIX="default"

# [ <name>:libp2p@version , ... ]
# NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1.2" "normal:v0.21.1-normal-v1")
NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1.5" "normal:v0.21.1-normal-v1.1")

# output binary
KUBO_OUTPUT_BIN=cmd/ipfs/ipfs

# common version for all new new kubo versions
LIBP2P_VERSION=v0.26.4-research
KBUCKET_VERSION=v0.5.1-research-v2.1

# dependecies name
LIBP2P=go-libp2p
KBUCKET=go-libp2p-kbucket
DHT=go-libp2p-kad-dht

# ------------------
#   Docker Images 
# ------------------

# webserver image name 
WSERVER_IMAGE=webmaster

# ipfs client binary (not a ipfs node)
CLIENT_BIN="ipfs-client"

# webserver and kubo docker file
KUBO_DFILE=./images/common/Dockerfile
BOOT_DFILE=./images/boot-nodes/Dockerfile

USAGE="usage: $0 [ --images | --bin | --all | --clean | --help ]"

# --------------------
#   Helper functions
# --------------------

function help(){
    # TODO: have a line for each one of the flags
    echo "$USAGE"
    exit 0
}

# receives the name suffix as argument
function build-kubo-bin(){
    local binary_name=$1

    echo -e "> building $binary_name..."

    go mod tidy
    make clean > /dev/null && GOOS='linux' make build 
    cp "$KUBO_OUTPUT_BIN" "$OUTBIN/$binary_name"

    echo
}

# set up default dependecies
function new-dht-default-depencies(){
    go mod edit -replace "github.com/libp2p/$LIBP2P"="github.com/JamesHertz/$LIBP2P@$LIBP2P_VERSION"
    go mod edit -replace "github.com/libp2p/$KBUCKET"="github.com/JamesHertz/$KBUCKET@$KBUCKET_VERSION"
}

function switch-dht-depency(){
    local new_version=$1
    go mod edit -replace "github.com/libp2p/$DHT"="github.com/JamesHertz/$DHT@$new_version"
}

# ------------------
#   Important Part
# ------------------

function build-binaries(){
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

    log "building root versions"
    pushd "$BOOT_REPO"
        build-kubo-bin "default-boot"

        IFS=':' read -ra values <<< "${NEW_KUBO_VERSIONS[1]}"

        # setup depencies
        new-dht-default-depencies 
        switch-dht-depency "${values[1]}"

        build-kubo-bin "upgradable-boot"
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

    log "building images..."

    for file in ./bin/ipfs-* ; do
        local binary_name=$(basename "$file")

        # if the binary is one of the versions (let's generate a docker image)
        if ! [ "$CLIENT_BIN"  = "$binary_name" ] ; then 

            # TODO: change the way you get the mode :)
            IFS='-' read -ra values <<< "$binary_name"
            local mode=${values[1]}

            echo -e "> building $binary_name" 
            docker build -t "$binary_name" \
                --build-arg "binary=$binary_name" \
                --build-arg "mode=$mode" --file "$KUBO_DFILE" . 
            echo
        fi
    done

    for file in ./bin/*-boot ; do
        local binary_name=$(basename "$file")

        IFS='-' read -ra values <<< "$binary_name"
        local setup=${values[0]}

        echo -e "> building $binary_name" 
        docker build -t "$binary_name" \
            --build-arg "setup=$setup" --file "$BOOT_DFILE" . 
        echo
    done


}

function main() {
    case $1 in
        --images) 
            build-images
        ;;

        --bin)
            build-binaries
        ;;

        --all|'')
            build-binaries
            build-images
        ;;

        --clean)
            log "cleaning unamed images"
            images=$(docker images --filter "dangling=true" -q --no-trunc)
            [ -n "$images" ] && docker rmi $images
            exit 0
        ;;

        --help)
            help 
        ;;

        *)
            echo -e "$USAGE\nError: Unknown flag: $1"
            exit 1
        ;;
    esac
    
    echo "----------------------------------" 
    echo "               DONE               "
    echo "----------------------------------" 
}

main "$@"
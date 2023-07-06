#! /usr/bin/env bash
set -e


# FIXME: ...
source utils.sh && cd ..


# ------------------
#   Binaries
# ------------------

OUTBIN=$PWD/bin

KUBO_REPO=./repos/kubo-ipfs
DEFAULT_KUBO_SUFFIX="default"

# [ <name>:libp2p@version , ... ]
NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1.2" "normal:v0.21.1-normal-v1")

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
WSERVER_DFILE=./images/master/Dockerfile
KUBO_DFILE=./images/common/Dockerfile

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
    local binary_name="ipfs-$1"

    echo -e "> building $binary_name..."

    go mod tidy
    make clean > /dev/null && GOOS='linux' make build 
    cp "$KUBO_OUTPUT_BIN" "$OUTBIN/$binary_name"

    echo
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

    log "building auxiliar binaries..."
    # generate ipfs-client and webmaster binaries
    for dir in ./repos/* ; do
        # skip kubo repo :)
        [ "$dir" = "$KUBO_REPO" ] && continue
        pushd "$dir"
            if [ -f Makefile ] ; then 
                echo "> building $dir"  
                make clean > /dev/null && GOOS='linux' make && cp bin/* "$OUTBIN"
            fi
        popd 
    done

    log "building kubo versions"
    # generate the default version 
    pushd "$KUBO_REPO" 
        build-kubo-bin "$DEFAULT_KUBO_SUFFIX"

        # set up default dependecies
        go mod edit -replace "github.com/libp2p/$LIBP2P"="github.com/JamesHertz/$LIBP2P@$LIBP2P_VERSION"
        go mod edit -replace "github.com/libp2p/$KBUCKET"="github.com/JamesHertz/$KBUCKET@$KBUCKET_VERSION"

        for version_info in ${NEW_KUBO_VERSIONS[@]}; do

            IFS=':' read -ra values <<< "$version_info"
            if ! [ ${#values[@]} -eq 2 ] ; then
                echo "Invalid version info: $values"
                exit 1
            fi

            local kubo_prefix=${values[0]}
            local dht_version=${values[1]}

            go mod edit -replace "github.com/libp2p/$DHT"="github.com/JamesHertz/$DHT@$dht_version"

            build-kubo-bin "$kubo_prefix"
        done

    popd 
}

function build-images(){

    log "building images..."

    echo "> building $WSERVER_IMAGE"
    docker build -t "$WSERVER_IMAGE" --file "$WSERVER_DFILE" .

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
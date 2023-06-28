#! /usr/bin/env bash
set -e

# ------------------
#   Binaries
# ------------------

OUTBIN=$PWD/bin

KUBO_REPO=./repos/kubo-ipfs
DEFAULT_KUBO_SUFFIX="default"

# [ <name>:libp2p@version , ... ]
NEW_KUBO_VERSIONS=("secure:v0.21.1-secure-v1" "normal:v0.21.1-normal ")

# output binary
KUBO_OUTPUT_BIN=cmd/ipfs/ipfs

# common version for all new new kubo versions
LIBP2P_VERSION=v0.26.4-research
KBUCKET_VERSION=v0.5.1-research-v2

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

function popd(){
    command popd $@ >> /dev/null 
}

function pushd(){
    command pushd $@ >> /dev/null
}

# receives the name suffix as argument
function build_kubo_bin(){
    local binary_name="ipfs-$1"

    echo -e "> building $binary_name..."

    go mod tidy
    make clean > /dev/null && GOOS='linux' make build 
    cp "$KUBO_OUTPUT_BIN" "$OUTBIN/$binary_name"

    echo
}

function log(){
    echo
    echo "$1"
    echo "-----------------------------------" 
    echo 
}

function build_binaries(){
    # if bin doesn't exists generate it :)
    ! [ -d "$OUTBIN" ] &&  mkdir "$OUTBIN"
    # delete everyting inside outbin
    rm -rf $OUTBIN/* 

    # get the most update version of everything
    log "reseting submodules..."
    git submodule foreach git reset --hard 

    log "pulling last submodules changes..."
    git pull --recurse-submodules 

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
        build_kubo_bin "$DEFAULT_KUBO_SUFFIX"

        # set up default dependecies
        go mod edit -replace "github.com/libp2p/$LIBP2P"="github.com/JamesHertz/$LIBP2P@$LIBP2P_VERSION"
        go mod edit -replace "github.com/libp2p/$KBUCKET"="github.com/JamesHertz/$KBUCKET@$KBUCKET_VERSION"

        for version_info in ${NEW_KUBO_VERSIONS[@]}; do

            IFS=':' read -ra values <<< "$version_info"
            if ! [ ${#values[@]} -eq 2 ] ; then
                echo "Invalid version info: $values"
                exit 1
            fi

            kubo_prefix=${values[0]}
            dht_version=${values[1]}

            go mod edit -replace "github.com/libp2p/$DHT"="github.com/JamesHertz/$DHT@$dht_version"

            build_kubo_bin "$kubo_prefix"
        done

    popd 
}

function build_images(){

    log "building images..."

    # echo "> building $WSERVER_IMAGE"
    # docker build -t "$WSERVER_IMAGE" --file "$WSERVER_DFILE" .
    # echo

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

function help(){
    echo "usage: ./build.sh [ --images | --bin | --all ] "
}

function main() {

    case $1 in
        --images) 
            build_images
        ;;
        --bin)
            build_binaries
        ;;
        --all|'')
            build_binaries
            build_images
        ;;
        --help)
            help ; exit 0
        ;;

        *)
            echo "Error: Unknown flag: $1"
            help ; exit 1
        ;;
    esac
    
    echo "----------------------------------" 
    echo "               DONE               "
    echo "----------------------------------" 
}

main "$@"

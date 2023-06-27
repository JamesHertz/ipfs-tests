#! /usr/bin/env bash
set -e

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

function popd(){
    command popd $@ >> /dev/null 
}

function pushd(){
    command pushd $@ >> /dev/null
}

# receives the name suffix as argument
function build_kubo_bin(){
    local binary_name="ipfs-$1"

    echo "building $binary_name..."

    go mod tidy
    make build 
    cp "$KUBO_OUTPUT_BIN" "$OUTBIN/$binary_name"
    echo "------------------------------------------------"
}

function log(){
    echo
    echo "$1"
    echo "-----------------------------------" 
    echo 
}

function main() {

    # if bin doesn't exists generate it :)
    ! [ -d "$OUTBIN" ] &&  mkdir "$OUTBIN"
    # delete everyting inside outbin
    rm -rf $OUTBIN/* 

    # get the most update version of everything
    log "reseting submodules..."
    git submodule foreach git reset --hard 

    log "pulling last changes submodules..."
    git pull --recurse-submodules 

    log "buildint auxiliar binaries"
    # generate ipfs-client and webmaster binaries
    for dir in ./repos/* ; do
        # skip kubo repo :)
        [ "$dir" = "$KUBO_REPO" ] && continue
        pushd "$dir"
            if [ -f Makefile ] ; then 
                echo "building $dir"  
                GOOS='linux' make --silent && cp bin/* "$OUTBIN"
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


    echo 
    echo "----------------------------------" 
    echo "               DONE               "
    echo "----------------------------------" 
    echo 
}

main "$@"

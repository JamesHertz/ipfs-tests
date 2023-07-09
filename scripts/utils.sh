
# shared dir on the host side
export SHARED_DIR=~/.ipfs-exp

# values used to generated repos and cids
export REPOS_NR=800
export FILES_NR=$((40*REPOS_NR))
# in megabytes
export FILE_SIZE=10

# used for formating
bold=$(tput bold)
normal=$(tput sgr0)

function popd(){
    command popd $@ >> /dev/null 
}

function pushd(){
    command pushd $@ >> /dev/null
}

function log(){
    echo -e "\n$1\n-----------------------"
}

function error(){
    echo -e "ERROR: $1"
    exit 1
}

function foreach-host(){
    local cmd=$1
    local v=

    [ -z "$cmd" ] && return 1
    [ "$2" = -v ] && v=1


    local curr_host=$(hostname)
    for host in `oarprint host`; do
        if [ "$host" != "$curr_host" ] ; then
            echo "> $host"

            local shcmd='oarsh "$host" "$cmd"'
            ! [ $v ] && shcmd="$shcmd > /dev/null"

            eval "$shcmd"
        fi
    done

    return 0
}

# if ! [ -d "$SHARED_DIR" ] ; then 
#     mkdir "$SHARED_DIR"
# fi
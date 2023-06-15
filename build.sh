#! /usr/bin/env bash
set -e
OUTBIN=$PWD/bin

! [ -d "$OUTBIN" ] &&  mkdir "$OUTBIN"

for dir in ./repos/* ; do
    pushd -q "$dir"
        [ -f Makefile ] && make --silent && cp bin/* "$OUTBIN"
    popd -q
done

echo "done"
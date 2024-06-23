#!/bin/bash

selfdir=$(dirname "$(readlink -f "$0")")

function j {
    python3 -u $selfdir/main.py
    ret=$?
    echo $ret > /tmp/out.1
    if [ $ret -eq 0 ]; then
        echo "ret is 0" > /tmp/out.2
        # jump the first path in the _recent now by sourceing _go script
        newpath=$(head -1 ~/.config/jcmd/recent)
        #echo "moving to $newpath"
        echo "cd \"$newpath\"" > $selfdir/_go
        source $selfdir/_go
        rm $selfdir/_go
        ls -lart
    elif [ $ret -eq 1 ]; then
        #echo "Stay"
    else
        echo "failed to run jcmd $?"
    fi
}


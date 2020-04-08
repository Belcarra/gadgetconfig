#!/bin/bash


for i in *.json
do


    echo 
    echo Checking $i

    (
    set -x
    gadgetconfig --remove-all
    gadgetconfig --add $i
    diff -bu $i <(gadgetconfig --export) | tee $i-diff
    [ -s $i-diff ] || rm $i-diff
    )
    # read i

done
gadgetconfig --remove-all



#!/bin/bash


for off in 0.5 1 1.5 2;
do
    for on in `seq 1 1 40`;
    do
	cat dat/base__settings.json | sed -e 's/@ON/'${on}'/g' | sed -e 's/@OFF/'${off}'/g' > dat/use.json
	invoke run --settingFile="dat/use.json"
    done
done

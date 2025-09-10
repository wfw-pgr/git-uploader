#!/bin/bash


for day in `seq 1 2 40`;
do
    sed -e 's/@DAY/'${day}'/g' dat/base__settings.json > dat/use.json
    invoke run --settingFile="dat/use.json"
done

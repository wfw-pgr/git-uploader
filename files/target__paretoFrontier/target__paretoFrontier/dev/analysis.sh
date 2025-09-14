#!/bin/bash

for dist in 4 8 12 16 20;
do
    for shift in 0 2 4 6;
    do
	cat dat/base__ri_prod__Ra226gn.json | sed -e "s/#ID#/dist${dist}mm_shift${shift}mm/g" > dat/ri_prod__Ra226gn__dist${dist}mm_shift${shift}mm.json
	python3 pyt/integrate__RIprodReaction.py --paramsFile dat/ri_prod__Ra226gn__dist${dist}mm_shift${shift}mm.json
    done
done

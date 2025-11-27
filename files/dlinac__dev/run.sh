#!/bin/bash

for factor in 1.0 0.95 0.90 0.85 0.80 0.75 0.70 0.65 0.60 0.55 0.50;
do
    sed -e "s/@factor/${factor}/g" dat/parameters_base.json > dat/parameters.json
    invoke all
    python pyt/plot__betaFunction.py
    cp -r png save/fb_${factor}
done

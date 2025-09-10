import os, sys, json5
import numpy  as np
import pandas as pd
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1

GBq        = 1.e9
outFile    = "dat/period_vs_annualProd.csv"
beamon     = [ int(val) for val in np.arange( 0.0, 40.1, 1.0 ) ]
beamoff    = 2

# ------------------------------------------------- #
# --- [1] data summary                          --- #
# ------------------------------------------------- #
filenames  = [ "dat/summary__{}d.json".format( ik ) for ik in beamon ]
stack      = []
for ifile in filenames:
    with open( ifile, "r" ) as f:
        hdict = json5.load( f )
    stack += [ hdict["normalized.Bcum"] ]
period     = np.array( beamon ) + beamoff
annual     = np.array( stack  ) / GBq
df         = pd.DataFrame( { "period[d]":period, "annual[GBq]":annual } )
df.to_csv( outFile, index=False )
print( "[analyze.py] output :: {} ".format( outFile ) )

# ------------------------------------------------- #
# --- [2] plot                                  --- #
# ------------------------------------------------- #
config     = lcf.load__config()
config_    = {
    "figure.size"        : [4.5,4.5],
    "figure.pngFile"     : "png/beamOn_vs_annualProd.png", 
    "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
    "ax1.y.normalize"    : 1.0e0, 
    "ax1.x.range"        : { "auto":False, "min": 0.0, "max":  40.0, "num":5 },
    "ax1.y.range"        : { "auto":False, "min": 0.0, "max":1000.0, "num":11 },
    "ax1.x.label"        : "Production Period [d]",
    "ax1.y.label"        : "Annual Production [GBq/y]",
    "ax1.x.minor.nticks" : 1, 
    "plot.marker"        : "o",
    "plot.markersize"    : 3.0,
    "legend.fontsize"    : 9.0, 
}
config = { **config, **config_ }
    
fig    = gp1.gplot1D( config=config )
fig.add__plot( xAxis=period, yAxis=annual )
fig.set__axis()
fig.save__figure()

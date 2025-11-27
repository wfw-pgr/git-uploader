import os,sys
import pandas as pd
import numpy  as np
import scipy  as sp
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1
import nk_toolkit.impactx.impactx_toolkit as itk

data = pd.read_csv( "dat/rf.csv", encoding="cp932", names=["zp","Ez","blank1","blank2"] )
print( data )

# volt = sp.integrate.simpson( data["Ez"], x=data["zp"] )
# data["Ez"] = data["Ez"] / volt
# print( volt/1e6, " [MV]" )

nMode = 6
ret  = itk.compute__fourierCoefficients( xp=data["zp"], fx=data["Ez"], nMode=nMode, \
                                         pngFile="png/rf_fourier.png", \
                                         coefFile="dat/rf_fourier.dat" )

modes = np.arange( nMode )

import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1

config   = lcf.load__config()
config_  = {
    "figure.size"        : [4.5,4.5],
    "figure.pngFile"     : "png/fourier_modes.png", 
    "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
    "ax1.y.normalize"    : 1.0e0, 
    "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
    "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
    "ax1.x.label"        : "modes",
    "ax1.y.label"        : "Coefficients",
    "ax1.x.minor.nticks" : 1, 
    "plot.marker"        : "o",
    "plot.markersize"    : 3.0,
    "legend.fontsize"    : 9.0, 
}
config = { **config, **config_ }
    
fig    = gp1.gplot1D( config=config )
fig.add__plot( xAxis=modes, yAxis=ret[:,0], label="cos" )
fig.add__plot( xAxis=modes, yAxis=ret[:,1], label="sin" )
fig.set__axis()
fig.set__legend()
fig.save__figure()

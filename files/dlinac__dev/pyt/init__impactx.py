import sys
import pandas as pd
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1

mm      = 10.0
inpFile = "impactx/diags/openPMD/bpm.h5"

import nk_toolkit.impactx.impactx_toolkit as itk
ret      = itk.load__impactHDF5( inpFile=inpFile, steps=[0] )
print( ret )
sys.exit()

config   = lcf.load__config()
config_  = {
    "figure.size"        : [4.5,4.5],
    "figure.pngFile"     : "png/init_track.png", 
    "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
    "ax1.y.normalize"    : 1.0e0, 
    "ax1.x.range"        : { "auto":False, "min": -200.0, "max":200.0, "num":11 },
    "ax1.y.range"        : { "auto":False, "min": -40.0, "max":40.0, "num":11 },
    "ax1.x.label"        : "x [mm]",
    "ax1.y.label"        : "x' [mrad]",
    "ax1.x.minor.nticks" : 1,
    "plot.linestyle"     : "none", 
    "plot.marker"        : "o",
    "plot.markersize"    : 0.5,
    "legend.fontsize"    : 9.0, 
}
config = { **config, **config_ }
    
fig    = gp1.gplot1D( config=config )
fig.add__plot( xAxis=xAxis, yAxis=yAxis )
fig.set__axis()
fig.save__figure()

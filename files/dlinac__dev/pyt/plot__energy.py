import pandas                       as pd
import nk_toolkit.plot.load__config as lcf
import nk_toolkit.plot.gplot1D      as gp1

inpFile = "impactx/diags/postProcessed_beam.csv"
data    = pd.read_csv( inpFile )
xAxis   = data["s_refp"]
yAxis   = data["Ek"]

config  = lcf.load__config()
config_ = {
    "figure.size"        : [10.5,3.5],
    "figure.pngFile"     : "png/s-Ek.png",
    "figure.position"    : [ 0.10, 0.15, 0.97, 0.93 ],
    "ax1.y.normalize"    : 1.0e0, 
    "ax1.x.range"        : { "auto":False, "min": 0.0, "max":80.0 , "num":9  },
    "ax1.y.range"        : { "auto":False, "min": 0.0, "max":200.0, "num":11 },
    "ax1.x.label"        : "s [m]",
    "ax1.y.label"        : "Energy [MeV]",
    "ax1.x.minor.nticks" : 1, 
    "plot.marker"        : "o",
    "plot.markersize"    : 3.0,
    "legend.fontsize"    : 9.0, 
}
config = { **config, **config_ }
    
fig    = gp1.gplot1D( config=config )
fig.add__plot( xAxis=xAxis, yAxis=yAxis, label="Kinetic Energy (MeV)" )
fig.set__axis()
fig.set__legend()
fig.save__figure()

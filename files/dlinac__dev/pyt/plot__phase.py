import pandas as pd
import nk_toolkit.plot.load__config as lcf
import nk_toolkit.plot.gplot1D      as gp1

inpFile = "impactx/diags/postProcessed_beam.csv"
data    = pd.read_csv( inpFile )
xAxis   = data["s_stat"]
phmin   = data["phase_min"]
phavg   = data["phase_avg"]
phmax   = data["phase_max"]

config   = lcf.load__config()
config_  = {
    "figure.size"        : [10.5,3.5],
    "figure.pngFile"     : "png/s-phase.png", 
    "figure.position"    : [ 0.10, 0.15, 0.97, 0.93 ],
    "ax1.x.range"        : { "auto":False, "min":    0.0, "max":80.0 , "num":9  },
    "ax1.y.range"        : { "auto":False, "min": -180.0, "max":180.0, "num":9 },
    "ax1.x.label"        : "s [m]",
    "ax1.y.label"        : "phase [deg]",
    "ax1.x.minor.nticks" : 1, 
    "plot.marker"        : "none",
    "plot.markersize"    : 3.0,
    "legend.fontsize"    : 9.0, 
}
config = { **config, **config_ }
    
fig    = gp1.gplot1D( config=config )
fig.add__plot( xAxis=xAxis, yAxis=phmin  , linestyle="-" , color="C0", label="min" )
fig.add__plot( xAxis=xAxis, yAxis=phavg  , linestyle="-" , color="C1", label="avg" )
fig.add__plot( xAxis=xAxis, yAxis=phmax  , linestyle="-" , color="C2", label="max" )
fig.add__plot( xAxis=xAxis, yAxis=phmin/4, linestyle="--", color="C0", label="min" )
fig.add__plot( xAxis=xAxis, yAxis=phavg/4, linestyle="--", color="C1", label="avg" )
fig.add__plot( xAxis=xAxis, yAxis=phmax/4, linestyle="--", color="C2", label="max" )
fig.set__axis()
fig.set__legend()
fig.save__figure()

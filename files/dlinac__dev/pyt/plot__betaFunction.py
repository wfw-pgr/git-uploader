import numpy  as np
import pandas as pd
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1
import nk_toolkit.impactx.impactx_toolkit as itk

cm   = 1.e-2
mrad = 1.e-3

separete = True

# ------------------------------------------------- #
# --- [1] input data                            --- #
# ------------------------------------------------- #
inpFile_t = "track/beam.out" 
inpFile_i = "impactx/diags/reduced_beam_characteristics.0" 
data_t    = pd.read_csv( inpFile_t, sep=r"\s+" )
data_i    = pd.read_csv( inpFile_i, sep=r"\s+" )


# ------------------------------------------------- #
# --- [2] data                                  --- #
# ------------------------------------------------- #
sleng_i   = data_i["s"]
betax_i   = data_i["beta_x"]
betay_i   = data_i["beta_y"]
betat_i   = data_i["beta_t"]
sleng_t   = data_t["dist[m]"]
betax_t   = data_t["b_x[cm/mrad]"] * cm / mrad
betay_t   = data_t["b_y[cm/mrad]"] * cm / mrad
betat_t   = data_t["b_z[deg/(%ofD_W/W)]"]


# ------------------------------------------------- #
# --- [3] config                                --- #
# ------------------------------------------------- #
config   = lcf.load__config()
config_  = {
    "figure.size"        : [10.5,3.5],
    "figure.position"    : [ 0.10, 0.15, 0.97, 0.93 ],
    "figure.pngFile"     : "png/s-beta__compare.png", 
    "ax1.y.normalize"    : 1.0e0, 
    "ax1.x.range"        : { "auto":False, "min": 0.0, "max":80.0, "num":9  },
    "ax1.y.range"        : { "auto":False, "min": 0.0, "max":30.0, "num":7 },
    "ax1.x.label"        : "s [m]",
    "ax1.y.label"        : r"$\beta$ [m]",
    "ax1.x.minor.nticks" : 1, 
    "plot.marker"        : "o",
    "plot.markersize"    : 3.0,
    "legend.fontsize"    : 9.0, 
}
config = { **config, **config_ }


# ------------------------------------------------- #
# --- [4] plot                                  --- #
# ------------------------------------------------- #
if not( separete ):
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=sleng_i, yAxis=betax_i, \
                   linestyle="-", color="C0", label=r"$\beta_x$ (impactX)" )
    fig.add__plot( xAxis=sleng_i, yAxis=betay_i, \
                   linestyle="-", color="C1", label=r"$\beta_y$ (impactX)" )
    # fig.add__plot( xAxis=sleng_i, yAxis=betat_i, \
    #                linestyle="-", color="C2", label=r"$\beta_t$ (impactX)" )
    fig.add__plot( xAxis=sleng_t, yAxis=betax_t, \
                   linestyle="--", color="C0", label=r"$\beta_x$ (TRACK)" )
    fig.add__plot( xAxis=sleng_t, yAxis=betay_t, \
                   linestyle="--", color="C1", label=r"$\beta_y$ (TRACK)" )
    # fig.add__plot( xAxis=sleng_t, yAxis=betat_t, \
    #                linestyle="--", label=r"$\beta_t$ (TRACK)" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

else:
    fig    = gp1.gplot1D( config=config, pngFile="png/s-beta__impactx.png" )
    fig.add__plot( xAxis=sleng_i, yAxis=betax_i, label=r"$\beta_x$ (impactX)" )
    fig.add__plot( xAxis=sleng_i, yAxis=betay_i, label=r"$\beta_y$ (impactX)" )
    itk.plot__lattice( latticeFile="dat/beamline_impactx.json", ax=fig.ax1, \
                       height=2.0, y0=26.0 )
    # fig.add__plot( xAxis=sleng_i, yAxis=betat_i, label=r"$\beta_t$ (impactX)" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

    fig    = gp1.gplot1D( config=config, pngFile="png/s-beta__track.png" )
    fig.add__plot( xAxis=sleng_t, yAxis=betax_t, label=r"$\beta_x$ (TRACK)" )
    fig.add__plot( xAxis=sleng_t, yAxis=betay_t, label=r"$\beta_y$ (TRACK)" )
    # fig.add__plot( xAxis=sleng_t, yAxis=betat_t, label=r"$\beta_t$ (TRACK)" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

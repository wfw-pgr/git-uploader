import os, sys, json5, h5py
import numpy  as np
import pandas as pd
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1
import nk_toolkit.impactx.io_toolkit  as itk

# ========================================================= #
# ===  main()                                           === #
# ========================================================= #

def main( bpmsFile=None, recoFile=None, refpFile=None ):

    for step in [ 1, 57, 113, 169, 225 ]:
        poincare__impactx( bpmsFile=bpmsFile, recoFile=recoFile, \
                           refpFile=refpFile, step=step )
        
    filebase = "track/coord.out.{:02}"
    for step in [ 0, 1, 2, 3, 4 ]:
        poincare__track( filebase=filebase, step=step )


# ========================================================= #
# ===  poincare__impactx                                === #
# ========================================================= #

def poincare__impactx( bpmsFile=None, recoFile=None, refpFile=None, step=None ):
    
    bpms_df = itk.get__particles( recoFile=recoFile, refpFile=refpFile, \
                                  bpmsFile=bpmsFile, steps=[step] )
    plot__poincareMap( bpms_df=bpms_df, tag="impactx", step=step )


# ========================================================= #
# ===  poincare__track                                  === #
# ========================================================= #

def poincare__track( filebase=None, step=None ):

    cm, mrad, ns, Nu = 1.e-2, 1.e-3, 1.e-9, 2.0

    coord_df       = pd.read_csv( filebase.format(step), sep=r"\s+" )
    bpms_df        = pd.DataFrame({
        "xp" : coord_df["x[cm]"]     * cm,
        "yp" : coord_df["y[cm]"]     * cm,
        "px" : coord_df["x'[mrad]"]  * mrad,
        "py" : coord_df["y'[mrad]"]  * mrad,
        "dt" : coord_df["dt[nsec]"]  * ns,
        "dEk": coord_df["dW[Mev/u]"] * Nu,
    })
    plot__poincareMap( bpms_df=bpms_df, tag="track", step=step )


# ========================================================= #
# ===  plot__poincareMap                                === #
# ========================================================= #

def plot__poincareMap( bpms_df=None, tag="impactx", step=0, plot_conf={} ):

    # ------------------------------------------------- #
    # --- [1] default config                        --- #
    # ------------------------------------------------- #
    def_conf = {
        **lcf.load__config(),
        "figure.size"        : [4.5,4.5],
        "figure.position"    : [ 0.18, 0.18, 0.92, 0.92 ],
        "ax1.x.minor.nticks" : 1,
        "ax1.x.range"        : { "auto":False, "min": -1.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":False, "min": -1.0, "max":1.0, "num":11 },
        "plot.linestyle"     : "none",
        "plot.marker"        : "o",
        "plot.markersize"    : 0.2,
        "legend.fontsize"    : 9.0,
    }
    pngbase = "png/poincare/{t}/{{}}_{:06}.png".format( step, t=tag )
    basedir = os.path.dirname( pngbase.format("_") )
    os.makedirs( basedir, exist_ok=True )

    # ------------------------------------------------- #
    # --- [2] plot settings                         --- #
    # ------------------------------------------------- #
    plots = {
        "xp-px": {
            "config": {
                "figure.pngFile" : pngbase.format("xp-px"),
                "ax1.x.label"    : "x (mm)",
                "ax1.y.label"    : "x' (mrad)",
                "ax1.x.range"    : { "auto":False, "min":-100.0, "max":100.0, "num":11 },
                "ax1.y.range"    : { "auto":False, "min":-100.0, "max":100.0, "num":11 },
                "ax1.x.normalize": 1.e-3,
                "ax1.y.normalize": 1.e-3,
            },
            "plots": [ { "xAxis":bpms_df["xp"], "yAxis":bpms_df["px"], "density":True } ],
        },
        "yp-py": {
            "config": {
                "figure.pngFile" : pngbase.format("yp-py"),
                "ax1.x.label"    : "y (mm)",
                "ax1.y.label"    : "y' (mrad)",
                "ax1.x.range"    : { "auto":False, "min":-100.0, "max":100.0, "num":11 },
                "ax1.y.range"    : { "auto":False, "min":-100.0, "max":100.0, "num":11 },
                "ax1.x.normalize": 1.e-3,
                "ax1.y.normalize": 1.e-3,
            },
            "plots": [ { "xAxis":bpms_df["yp"], "yAxis":bpms_df["py"], "density":True } ],
        },
        "dt-dE": {
            "config": {
                "figure.pngFile" : pngbase.format("dt-dE"),
                "ax1.x.label"    : "dt (ns)",
                "ax1.y.label"    : "dE (MeV)",
                "ax1.x.range"    : { "auto":False, "min": -2.0, "max": 2.0, "num":11 },
                "ax1.y.range"    : { "auto":False, "min": -2.0, "max": 2.0, "num":11 },
                "ax1.x.normalize": 1.e-9,
                "ax1.y.normalize": 1.e0,
            },
            "plots": [ { "xAxis":bpms_df["dt"], "yAxis":bpms_df["dEk"], "density":True } ],
        },
    }

    # ------------------------------------------------- #
    # --- [3] plot                                  --- #
    # ------------------------------------------------- #
    for key, contents in plots.items():
        config = { **def_conf, **(contents["config"]) }
        if key in plot_conf:
            config = { **config, **plot_conf[key] }
        fig = gp1.gplot1D( config=config )
        for plot in contents["plots"]:
            fig.add__scatter( **plot )
        fig.set__axis()
        fig.save__figure()


# ========================================================= #
# ===   Execution of Program                            === #
# ========================================================= #

if ( __name__=="__main__" ):

    main( bpmsFile = "impactx/diags/openPMD/bpm.h5",
          recoFile = "impactx/diags/records.json",
          refpFile = "impactx/diags/ref_particle.0" )

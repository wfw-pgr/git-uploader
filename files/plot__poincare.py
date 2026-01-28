import os, sys, json5, h5py
import numpy  as np
import pandas as pd
import matplotlib.pyplot  as plt
import matplotlib.patches as patches
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1
import nk_toolkit.impactx.io_toolkit  as itk


# ========================================================= #
# ===  main()                                           === #
# ========================================================= #

def main( bpmsFile=None, recoFile=None, refpFile=None, steps=None ):

    
    
    for step in steps:
        bpms_df = itk.get__particles( recoFile=recoFile, refpFile=refpFile, bpmsFile=bpmsFile, \
                                      steps=[step] )
        plot__poincare( bpms_df=bpms_df, step=step )

    steps    = [ 0, 1, 2, 3, 4 ]
    filebase = "track/ex17__260113_poincare_1A/coord.out.{:02}"
    
    for step in steps:
        plot__poincare__TRACKv38( filebase=filebase, step=step )


        
# ========================================================= #
# ===  plot__poincare                                   === #
# ========================================================= #

def plot__poincare( bpms_df=None, step=None, plot_conf={}  ):

    if ( bpms_df is None ): sys.exit( "[plot_poincare] bpms_df == ???" )
    if ( step    is None ):
        steps = list( set(bpms_df["step"]) )
        step  = sorted( steps )[0]
        if ( len( steps ) > 1 ):
            print( "[plot__poincare] #. of steps > 1.... " )
            print( " steps :: ", steps )
            sys.exit()

    # ------------------------------------------------- #
    # --- [2] plot config                           --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    def_conf = {
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
    def_conf = { **config, **def_conf }

    # ------------------------------------------------- #
    # --- [3] plots settings                        --- #
    # ------------------------------------------------- #
    plots      = {
        "xp-px": {
            "config":{
                "figure.pngFile" :"png/poincare__xp-px_step{:06}.png".format( step ), \
                "ax1.x.label"    : "x (mm)", \
                "ax1.y.label"    : "x' (mrad)", \
                "ax1.x.range"    : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.y.range"    : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.x.normalize": 1.e-3,
                "ax1.y.normalize": 1.e-3,
            }, \
            "plots": [ { "xAxis":bpms_df["xp"], "yAxis":bpms_df["px"] , "density":True }, ],
        }, \
        "yp-py": {
            "config":{
                "figure.pngFile"  :"png/poincare__yp-py_step{:06}.png".format( step ), \
                "ax1.x.label"     : "y (mm)", \
                "ax1.y.label"     : "y' (mrad)", \
                "ax1.x.range"     : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.y.range"     : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.x.normalize" : 1.e-3,
                "ax1.y.normalize" : 1.e-3,
            }, \
            "plots": [ { "xAxis":bpms_df["yp"], "yAxis":bpms_df["py"] , "density":True }, ],
        }, \
        "tp-pt": {
            "config":{
                "figure.pngFile"  :"png/poincare__tp-pt_step{:06}.png".format( step ), \
                "ax1.x.label"     : "t (mm)", \
                "ax1.y.label"     : "t' (mrad)", \
                "ax1.x.range"     : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.y.range"     : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.x.normalize" : 1.e-3,
                "ax1.y.normalize" : 1.e-3,
            }, \
            "plots": [ { "xAxis":bpms_df["tp"], "yAxis":bpms_df["pt"] , "density":True }, ],
        }, \
        "dt-pE": {
            "config":{
                "figure.pngFile"  :"png/poincare__dt-dE_step{:06}.png".format( step ), \
                "ax1.x.label"     : "dt (ns)", \
                "ax1.y.label"     : "dE (MeV)", \
                "ax1.x.range"     : { "auto":False, "min": -10.0, "max": 10.0, "num":11 },
                "ax1.y.range"     : { "auto":False, "min": -10.0, "max": 10.0, "num":11 },
                "ax1.x.normalize" : 1.e-9,
                "ax1.y.normalize" : 1.e0,
            }, \
            "plots": [ { "xAxis":bpms_df["dt"], "yAxis":bpms_df["dEk"] , "density":True }, ],
        }, \
    }
    
    # ------------------------------------------------- #
    # --- [3] plot                                  --- #
    # ------------------------------------------------- #
    for key,contents in plots.items():
        config = { **def_conf, **(contents["config"]) }
        if ( key in plot_conf ):
            config = { **config, **plot_conf[key] }
        fig = gp1.gplot1D( config=config )
        for plot in contents["plots"]:
            fig.add__scatter( **plot )
        fig.set__axis()
        fig.save__figure()


# ========================================================= #
# ===  plot__poincare__TRACKv38                         === #
# ========================================================= #

def plot__poincare__TRACKv38( bpms_df=None, step=None, plot_conf={}, filebase="" ):

    cm             = 1.0e-2
    mrad           = 1.0e-3
    ns             = 1.0e-9
    Nu             = 2.0
    
    inpFile        = filebase.format( step )
    coord_df       = pd.read_csv( inpFile, sep=r"\s+" )

    bpms_df        = {}
    bpms_df["xp"]  = coord_df["x[cm]"]     * cm
    bpms_df["yp"]  = coord_df["y[cm]"]     * cm
    bpms_df["px"]  = coord_df["x'[mrad]"]  * mrad
    bpms_df["py"]  = coord_df["y'[mrad]"]  * mrad
    bpms_df["dt"]  = coord_df["dt[nsec]"]  * ns
    bpms_df["dEk"] = coord_df["dW[Mev/u]"] * Nu
    bpms_df        = pd.DataFrame( bpms_df )

    # ------------------------------------------------- #
    # --- [2] plot config                           --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    def_conf = {
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
    def_conf = { **config, **def_conf }

    # ------------------------------------------------- #
    # --- [3] plots settings                        --- #
    # ------------------------------------------------- #
    plots      = {
        "xp-px": {
            "config":{
                "figure.pngFile" :"png/poincare__track_xp-px_step{:06}.png".format( step ), \
                "ax1.x.label"    : "x (mm)", \
                "ax1.y.label"    : "x' (mrad)", \
                "ax1.x.range"    : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.y.range"    : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.x.normalize": 1.e-3,
                "ax1.y.normalize": 1.e-3,
            }, \
            "plots": [ { "xAxis":bpms_df["xp"], "yAxis":bpms_df["px"] , "density":True }, ],
        }, \
        "yp-py": {
            "config":{
                "figure.pngFile"  :"png/poincare__track_yp-py_step{:06}.png".format( step ), \
                "ax1.x.label"     : "y (mm)", \
                "ax1.y.label"     : "y' (mrad)", \
                "ax1.x.range"     : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.y.range"     : { "auto":False, "min": -100.0, "max":100.0, "num":11 },
                "ax1.x.normalize" : 1.e-3,
                "ax1.y.normalize" : 1.e-3,
            }, \
            "plots": [ { "xAxis":bpms_df["yp"], "yAxis":bpms_df["py"] , "density":True }, ],
        }, \
        "dt-pE": {
            "config":{
                "figure.pngFile"  :"png/poincare__track_dt-dE_step{:06}.png".format( step ), \
                "ax1.x.label"     : "dt (ns)", \
                "ax1.y.label"     : "dE (MeV)", \
                "ax1.x.range"     : { "auto":False, "min": -10.0, "max": 10.0, "num":11 },
                "ax1.y.range"     : { "auto":False, "min": -10.0, "max": 10.0, "num":11 },
                "ax1.x.normalize" : 1.e-9,
                "ax1.y.normalize" : 1.e0,
            }, \
            "plots": [ { "xAxis":bpms_df["dt"], "yAxis":bpms_df["dEk"] , "density":True }, ],
        }, \
    }
    
    # ------------------------------------------------- #
    # --- [3] plot                                  --- #
    # ------------------------------------------------- #
    for key,contents in plots.items():
        config = { **def_conf, **(contents["config"]) }
        if ( key in plot_conf ):
            config = { **config, **plot_conf[key] }
        fig = gp1.gplot1D( config=config )
        for plot in contents["plots"]:
            fig.add__scatter( **plot )
        fig.set__axis()
        fig.save__figure()

        

# ========================================================= #
# ===  plot__poincare                                   === #
# ========================================================= #

def plot__poincare2( bpms=None, step=None, ):

    mm, mrad  = 1.0e-3, 1.0e-3
    cv, nsec  = 2.99792458e8, 1.0e-9
    
    if ( bpms is None ): sys.exit( "[plot_poincare] bpms == ???" )
    if ( step is None ): step = sorted( list( set(bpms["step"]) ) )[0]
    if ( type(bpms) is str ):
        bpms = h5py.File( bpms, "r" )

    # ------------------------------------------------- #
    # --- [1] prepare variables                     --- #
    # ------------------------------------------------- #
    if ( type(bpms) is pd.DataFrame ):
        bpms_        = bpms.loc[ bpms["step"] == step ].copy()
        bpms_["xp"]  = bpms_["xp"] / mm
        bpms_["yp"]  = bpms_["yp"] / mm
        bpms_["tp"]  = bpms_["tp"] / mm
        bpms_["px"]  = bpms_["px"] / mrad
        bpms_["py"]  = bpms_["py"] / mrad
        bpms_["pt"]  = bpms_["pt"] / mrad
        bpms_["dt"]  = bpms_["dt"] / nsec  # [ns]
        bpms_["dEk"] = bpms_["dEk"]        # [MeV]

    axpMax = np.max( [ np.abs( bpms_["xp"].min() ), np.abs( bpms_["xp"].max() ) ] )
    aypMax = np.max( [ np.abs( bpms_["yp"].min() ), np.abs( bpms_["yp"].max() ) ] )
    atpMax = np.max( [ np.abs( bpms_["tp"].min() ), np.abs( bpms_["tp"].max() ) ] )
    apxMax = np.max( [ np.abs( bpms_["px"].min() ), np.abs( bpms_["px"].max() ) ] )
    apyMax = np.max( [ np.abs( bpms_["py"].min() ), np.abs( bpms_["py"].max() ) ] )
    aptMax = np.max( [ np.abs( bpms_["pt"].min() ), np.abs( bpms_["pt"].max() ) ] )
    adtMax = np.max( [ np.abs( bpms_["dt"].min() ), np.abs( bpms_["dt"].max() ) ] )
    adEMax = np.max( [ np.abs( bpms_["dEk"].min() ), np.abs( bpms_["dEk"].max() ) ] )
    
    # ------------------------------------------------- #
    # --- [2] plot config                           --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    def_conf = {
        "figure.size"        : [4.5,4.5],
        "figure.position"    : [ 0.18, 0.18, 0.92, 0.92 ],
        "ax1.x.minor.nticks" : 1, 
        "plot.linestyle"     : "none", 
        "plot.marker"        : "o",
        "plot.markersize"    : 0.2,
        "legend.fontsize"    : 9.0, 
    }
    def_conf = { **config, **def_conf }

    config_ = {
        "xp-px" : {
            "figure.pngFile"     : "png/poincare__xp-px_step{:06}.png".format( step ), 
            "ax1.x.range"        : { "auto":False, "min": -axpMax, "max":axpMax, "num":11 },
            "ax1.y.range"        : { "auto":False, "min": -apxMax, "max":apxMax, "num":11 },
            "ax1.x.label"        : "x (mm)",
            "ax1.y.label"        : "x' (mrad)",
        },
        "yp-py" : {
            "figure.pngFile"     : "png/poincare__yp-py_step{:06}.png".format( step ), 
            "ax1.x.range"        : { "auto":False, "min": -aypMax, "max":+aypMax, "num":11 },
            "ax1.y.range"        : { "auto":False, "min": -apyMax, "max":+apyMax, "num":11 },
            "ax1.x.label"        : "y (mm)",
            "ax1.y.label"        : "y' (mrad)",
        },
        "tp-pt" : {
            "figure.pngFile"     : "png/poincare__tp-pt_step{:06}.png".format( step ), 
            "ax1.x.range"        : { "auto":False, "min": -atpMax, "max":+atpMax, "num":11 },
            "ax1.y.range"        : { "auto":False, "min": -aptMax, "max":+aptMax, "num":11 },
            "ax1.x.label"        : "t (mm)",
            "ax1.y.label"        : "t' (mrad)",
        },
        "dt-dE" : {
            "figure.pngFile"     : "png/poincare__dt-dE_step{:06}.png".format( step ), 
            "ax1.x.range"        : { "auto":False, "min": -adtMax, "max":+adtMax, "num":11 },
            "ax1.y.range"        : { "auto":False, "min": -adEMax, "max":+adEMax, "num":11 },
            "ax1.x.label"        : "dt (ns)",
            "ax1.y.label"        : "dE (MeV)",
        },
    }
    # ------------------------------------------------- #
    # --- [3] plots settings                        --- #
    # ------------------------------------------------- #
    plots      = {
        "xp-px": [ { "xAxis":bpms_["xp"], "yAxis":bpms_["px"] , "density":True }, ], \
        "yp-py": [ { "xAxis":bpms_["yp"], "yAxis":bpms_["py"] , "density":True }, ], \
        "tp-pt": [ { "xAxis":bpms_["tp"], "yAxis":bpms_["pt"] , "density":True }, ], \
        "dt-dE": [ { "xAxis":bpms_["dt"], "yAxis":bpms_["dEk"], "density":True }, ], \
    }
    
    # ------------------------------------------------- #
    # --- [3] plot                                  --- #
    # ------------------------------------------------- #
    for key,contents in plots.items():
        config = { **def_conf, **config_[key] }
        fig = gp1.gplot1D( config=config )
        for content in contents:
            fig.add__scatter( **content )
        fig.set__axis()
        fig.save__figure()



# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):

    bpmsFile = "impactx/diags/openPMD/bpm.h5"
    recoFile = "impactx/diags/records.json"
    refpFile = "impactx/diags/ref_particle.0"
    steps    = [ 1, 25, 49, 73 ]
    
    main( bpmsFile=bpmsFile, recoFile=recoFile, refpFile=refpFile, steps=steps )

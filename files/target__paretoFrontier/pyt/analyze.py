import os, sys
import json5
import numpy  as np
import pandas as pd
import scipy.special  as spc
import scipy.optimize as opt
import scipy.stats    as sta
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1

d_, s_, y_ = 0, 1, 2
dlist      = [ 4, 8, 12, 16, 20 ]
slist      = [ 0, 2, 4, 6 ]
Dlist      = [ 3, 5, 7 ]
wlist      = [ 4, 5, 6 ]
nColumns   = 5


# ========================================================= #
# ===  analyze.py                                       === #
# ========================================================= #

def extract__efficiency():
    
    # ------------------------------------------------- #
    # --- [1] extract efficiency                    --- #
    # ------------------------------------------------- #
    stack = []
    for w in wlist:
        for D in Dlist:
            for d in dlist:
                for s in slist:
                    ifile = "results/D{0}mm_FWHM{1}mm/results__Ra226gn__dist{2}mm_shift{3}mm.json"\
                        .format( D, w, d, s )
                    with open( ifile, "r" ) as f:
                        res    = json5.load( f )
                        val    = res["Yn_product_Bq"]
                        stack += [ [ D, w, d, s, val ] ]
    effs    = np.array( stack )
    
    # ------------------------------------------------- #
    # --- [2] data frame                            --- #
    # ------------------------------------------------- #
    outFile = "dat/yieldmap.csv"
    df      = pd.DataFrame( effs, columns=[ "Diameter", "FWHM", "dist", \
                                            "shift[mm]","yield[Bq/Bq/uA/s]"] )
    df.to_csv( outFile, index=False )

    # ------------------------------------------------- #
    # --- [3] plot efficiency                       --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/efficiency.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":False, "min": -2.0, "max":10.0, "num":7  },
        "ax1.y.range"        : { "auto":False, "min":  0.0, "max":2.e-8, "num":11 },
        "ax1.x.label"        : "shift [mm]",
        "ax1.y.label"        : "Efficiency [Bq/Bq/uA/s]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 6.0, 
    }
    config = { **config, **config_ }
    fig    = gp1.gplot1D( config=config )
    for ii,D in enumerate(Dlist):
        for ij,w in enumerate(wlist):
            for ik,d in enumerate(dlist):
                df_ = df [ df ["Diameter"] == D ]
                df_ = df_[ df_["FWHM"]     == w ]
                df_ = df_[ df_["dist"]     == d ]
                fig.add__plot( xAxis=df_["shift[mm]"], yAxis=df_["yield[Bq/Bq/uA/s]"], \
                               label="d={0}, FWHM={1}, D={2}".format(d,w,D) )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()
    return()


# ========================================================= #
# ===  fit__to_gaussian                                 === #
# ========================================================= #

def fit__to_gaussian():

    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    inpFile = "dat/yieldmap.csv"
    df      = pd.read_csv( inpFile )

    # ------------------------------------------------- #
    # --- [2] fit to gaussian                       --- #
    # ------------------------------------------------- #
    def gaussf( x, a0, a2 ):
        ret = a0*np.exp( (-0.5)*(x/a2)**2 )
        return( ret )
    def fit_group( grp ):
        grp    = grp.sort_values("shift[mm]")
        xval   = grp["shift[mm]"]        .to_numpy()
        yval   = grp["yield[Bq/Bq/uA/s]"].to_numpy()
        pop, _ = opt.curve_fit( gaussf, xval, yval )
        ret    = pd.Series( { "a0":pop[0], "a2":abs(pop[1]) } )
        return( ret )
    fits = ( df.groupby(["FWHM","Diameter","dist"])\
             [['shift[mm]','yield[Bq/Bq/uA/s]']]\
             .apply( fit_group ).reset_index() )

    # ------------------------------------------------- #
    # --- [4] save fit coeffs                       --- #
    # ------------------------------------------------- #
    fits.to_csv( "dat/fit_coefs.csv", index=False )
    return( fits )


# ========================================================= #
# ===  display__fittings                                === #
# ========================================================= #

def display__fittings():

    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    fitted = pd.read_csv( "dat/fit_coefs.csv" )
    sims   = pd.read_csv( "dat/yieldmap.csv"  )
    coefs  = { k: g for k, g in fitted.groupby([ 'FWHM', 'Diameter', 'dist' ] ) }
    simds  = { k: g for k, g in   sims.groupby([ 'FWHM', 'Diameter', 'dist' ] ) }
    
    def gaussf( x, a0, a2 ):
        ret = a0*np.exp( (-0.5)*(x/a2)**2 )
        return( ret )
    
    # ------------------------------------------------- #
    # --- [2] configs                               --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":False, "min": 0.0, "max":10.0  , "num":6  }, 
        "ax1.y.range"        : { "auto":False, "min": 0.0, "max":2.0e-8, "num":11 }, 
        "ax1.x.label"        : "shift [mm]",
        "ax1.y.label"        : "Yield [Bq/Bq/uA/s]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 8.0, 
    }
    config = { **config, **config_ }

    # ------------------------------------------------- #
    # --- [3] plot                                  --- #
    # ------------------------------------------------- #
    sAxis = np.linspace( -10.0, +10.0, 101 )
    for wval in wlist:
        for Dval in Dlist:
            pngFile = "png/fitting_D{0}mm_FWHM{1}mm.png".format( Dval, wval )
            fig     = gp1.gplot1D( config=config, pngFile=pngFile )
            for ik,dval in enumerate(dlist):
                args   = ( wval, Dval, dval )
                df1    = coefs.get( args )
                df2    = simds.get( args )
                fitv   = gaussf( sAxis, df1["a0"].iloc[0], df1["a2"].iloc[0] )
                fig.add__plot( xAxis=sAxis, yAxis=fitv, \
                               marker="none", linestyle="-", color=f"C{ik}" )
                fig.add__plot( xAxis=df2["shift[mm]"], yAxis=df2["yield[Bq/Bq/uA/s]"], \
                               marker="o", linestyle="none", color=f"C{ik}" )
            fig.set__axis()
            fig.save__figure()

            

# ========================================================= #
# === E[Y], V[Y] mapping                                === #
# ========================================================= #

def calculate__risk_return( sigma_b=1.0, Yreq_A0=0.90, csvFile="dat/risk_return.csv" ):

    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    coefs   = pd.read_csv( "dat/fit_coefs.csv" )
    dias    = coefs["Diameter"].to_numpy()
    fwhm    = coefs["FWHM"].to_numpy()
    dist    = coefs["dist"].to_numpy()
    A0      = coefs["a0"].to_numpy()
    wy      = coefs["a2"].to_numpy()

    # ------------------------------------------------- #
    # --- [2] calculate E[Y], V[Y]                  --- #
    # ------------------------------------------------- #
    r_sigma = sigma_b / wy
    EY      = A0 / np.sqrt( 1.0 + r_sigma**2 )
    EY2     = A0**2 / np.sqrt( 1.0 + 2.0 * r_sigma**2 )
    VY      = EY2 - EY**2
    sigmaY  = np.sqrt( VY )

    # ------------------------------------------------- #
    # --- [3] miss probability                      --- #
    # ------------------------------------------------- #
    t_beam        = wy / sigma_b * np.sqrt( np.log( 1.0/Yreq_A0 ) )
    Pmiss         = spc.erfc( t_beam )

    # ------------------------------------------------- #
    # --- [4] E[L] : expected loss                  --- #
    # ------------------------------------------------- #
    eps   = 1e-16
    Yreq  = Yreq_A0 * A0
    with np.errstate(divide='ignore', invalid='ignore'):
        z_t    = ( Yreq - EY ) / np.where( sigmaY > 0, sigmaY, np.nan )
        p_loss = sta.norm.cdf( z_t )           #  P( Y<Yreq )
        p_loss = np.where( np.isnan(p_loss), 0.0, p_loss )
    # conditional E[Y | Y < Yreq] under normal
    phi_t    = sta.norm.pdf(z_t)
    Phi_t    = p_loss.copy()
    Phi_safe = np.maximum(Phi_t, eps)
    EY_cond  = np.empty_like( EY )
    # degenerate sigma=0 case
    deg             = sigmaY < 1e-12
    EY_cond[deg]    = EY[deg]   # point mass; if EY < Yreq then L=Yreq-EY else no loss
    nondeg          = ~deg
    EY_cond[nondeg] = EY[nondeg] - sigmaY[nondeg] * (phi_t[nondeg] / Phi_safe[nondeg])

    # E[L | L>0] and E[L]
    EL_given_loss   = np.maximum( 0.0, Yreq-EY_cond )
    EL              = p_loss * EL_given_loss
    
    # ------------------------------------------------- #
    # --- [5] return                                --- #
    # ------------------------------------------------- #
    df = pd.DataFrame( { "Diameter":dias, "FWHM":fwhm, "dist":dist, 
                         "EY":EY, "EY2":EY2, "VY":VY, "sigmaY":sigmaY, "Pmiss":Pmiss, \
                         "EL":EL, \
                                   } )
    df["sigma_b"] = sigma_b
    if ( csvFile is not None ):
        df.to_csv( csvFile, index=False )
        print( "[analyze.py] output :: {} ".format( csvFile ) )
    return( df )


# ========================================================= #
# ===  display__riskReturn.py                           === #
# ========================================================= #

def display__risk_return( data=None, pareto=None, pngFile=None ):
    
    # ------------------------------------------------- #
    # --- [1] plot fitted map                       --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/Pmiss-EY.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True , "min":  0.0, "max":0.20   , "num":6 },
        "ax1.y.range"        : { "auto":False, "min":  0.0, "max":1.6e-8 , "num":9 },
        "ax1.x.label"        : r"$P(Y<Y_{c})$", 
        "ax1.y.label"        : r"$E[Y]$",
        "ax1.x.minor.nticks" : 5, 
        "plot.marker"        : "o",
        "plot.linestyle"     : "none",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 7.0, 
    }
    config  = { **config, **config_ }
    
    grp     = { k: g for k, g in data.groupby([ 'FWHM', 'Diameter' ] ) }
    args    = [ (4,3), (4,5), (4,7), (5,3), (5,5), (5,7), (6,3), (6,5), (6,7) ]
    fig     = gp1.gplot1D( config=config, pngFile=pngFile )
    for ia,arg in enumerate( args ):
        val  = grp.get( arg )
        fig.add__plot( xAxis=val["Pmiss"], yAxis=val["EY"], label="FWHM{0}mm D{1}mm".format( arg[0], arg[1] ) )
    if ( pareto is not None ):
        fig.add__plot( xAxis=pareto["xn"], yAxis=pareto["yn"], color="cyan", linestyle="--", marker="none", label="Pareto Frontier"    )
        fig.add__plot( xAxis=pareto["xe"], yAxis=pareto["ye"], color="red" , linestyle="none", marker="o" , label="knee point" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()
    return()

# ========================================================= #
# ===  extract__paretoFrontier                          === #
# ========================================================= #

def get__paretoFrontier( df=None, fit_type="quantile_regression", label=None ):

    # ------------------------------------------------- #
    # --- [1] extract__paretoFrontier               --- #
    # ------------------------------------------------- #
    def extract__paretoFrontierPoints( df=None, xkey=None, ykey=None ):
        df_  = df[ [xkey,ykey] ].copy()
        df_  = df_.sort_values( [ xkey, ykey ], ascending=[ True, False ] ).reset_index()
        df_  = df_.drop_duplicates( subset=[xkey], keep='first' )
        idx  = []
        maxE = (-1.0 * np.inf)
        for _, row in df_.iterrows():
            if ( row[ ykey ] > maxE ):
                idx  += [ row["index"] ]
                maxE  = row[ ykey ]
        ret = df.loc[idx].copy()
        ret = ret.sort_values( xkey ).reset_index( drop=True )
        return( ret )

    # ------------------------------------------------- #
    # --- [2] fittings of paretoFrontier            --- #
    # ------------------------------------------------- #
    pareto = extract__paretoFrontierPoints( df=df, xkey="Pmiss", ykey="EY" )
    xvals  = pareto["Pmiss"].to_numpy()
    yvals  = pareto["EY"].to_numpy()
    xnews  = np.linspace( np.min( xvals ), np.max( xvals ), 101 )

    # ------------------------------------------------- #
    # --- [3] 5th-order fittings                    --- #
    # ------------------------------------------------- #
    def polynomial_fit( xnews, xvals, yvals ):
        def polynomial_func( x, a5, a4, a3, a2, a1, a0 ):
            ret = a5*x**5 + a4*x**4 + a3*x**3 + a2*x**2 + a1*x + a0
            return( ret )
        pop, _ = opt.curve_fit( polynomial_func, xvals, yvals )
        func   = lambda x: polynomial_func( x, *pop )
        ynews  = func( xnews )
        return( ynews )

    # ------------------------------------------------- #
    # --- [4] quantile_regression                   --- #
    # ------------------------------------------------- #
    def quantile_regression( xnews, xvals, yvals ):
        import statsmodels.api as sm
        import patsy
        dof   = 3
        tau   = 0.97
        Xspl  = patsy.dmatrix( f"bs( xvals, df={dof}, include_intercept=False)",
                               { "xvals": xvals }, return_type="dataframe" )
        X     = sm.add_constant( Xspl )
        mod   = sm.QuantReg( yvals, X )
        res   = mod.fit( q=tau )
        Xg    = sm.add_constant( patsy.dmatrix( f"bs(xnews, df={dof}, include_intercept=False)", 
                                                { "xnews": xnews }, return_type='dataframe') )
        ynews = res.predict( Xg )
        return( ynews )

    # ------------------------------------------------- #
    # --- [5] isotonic pchip interpolation          --- #
    # ------------------------------------------------- #
    def isotonic_pchip( xnews, xvals, yvals ):
        import scipy.interpolate
        from sklearn.isotonic import IsotonicRegression
        ir = IsotonicRegression( increasing=True )
        E_iso = ir.fit_transform( xvals, yvals )   # P must be 1D ascending
        func   = scipy.interpolate.PchipInterpolator( xvals, E_iso )
        ynews  = func( xnews )
        return( ynews )

    # ------------------------------------------------- #
    # --- [6] call interpolator                     --- #
    # ------------------------------------------------- #
    if ( fit_type == "polynomial" ):
        ynews = polynomial_fit( xnews, xvals, yvals )
    if ( fit_type == "quantile_regression" ):
        ynews = quantile_regression( xnews, xvals, yvals )
    if ( fit_type == "isotonic_pchip" ):
        ynews = isotonic_pchip( xnews, xvals, yvals )
    return( xnews, ynews )


# ========================================================= #
# ===  find__elbowpoints                                === #
# ========================================================= #

def find__elbowPoints( xnews, ynews, method="distance", spline_s=0.0, return_all=False ):
    
    x = np.asarray( xnews )
    y = np.asarray( ynews )
    n = len(x)
    if ( method == "distance" ):
        def norm01(a):
            mn, mx = np.min(a), np.max(a)
            if mx - mn == 0:
                return np.zeros_like(a)
            return (a - mn) / (mx - mn)
        xn     = norm01(x)
        yn     = norm01(y)
        x1, y1 = xn[0], yn[0]
        x2, y2 = xn[-1], yn[-1]
        dx, dy = x2 - x1, y2 - y1
        denom  = np.hypot(dx, dy) + 1e-18        
        dists  = np.abs(dx*(y1 - yn) - dy*(x1 - xn)) / denom
        idx    = int( np.argmax( dists ) )
        return ( x[idx], y[idx] )

    elif ( method == "curvature" ):
        sp     = UnivariateSpline(x, y, s=spline_s, k=3)
        xg     = x
        y1     = sp.derivative(1)(xg)
        y2     = sp.derivative(2)(xg)
        denom  = (1.0 + y1**2)**1.5
        denom  = np.maximum(denom, 1e-18)
        kappa  = np.abs(y2) / denom
        idx    = int( np.argmax(kappa) )
        return( x[idx], y[idx] )

    elif ( method == "second" ):
        dy_dx  = np.gradient(y, x)
        d2y    = np.gradient(dy_dx, x)
        idx    = int(np.argmax(np.abs(d2y)))
        result = {"method":"second", "d2y": d2y}
        return( x[idx], y[idx] )



# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):

    sigma_bs = [ 0.6, 0.8, 1.0, 1.2, 1.6, 2.0 ]

    # extract__efficiency()
    # fit__to_gaussian()
    # display__fittings()
    # calculate__risk_return()

    # def multiple__analyze():
    #     stack    = []
    #     for ik,sb in enumerate( sigma_bs ):
    #         ret    = calculate__risk_return( sigma_b=sb, csvFile=None )
    #         stack += [ ret ]
    #     data = pd.concat( stack, axis=0 )
    #     data.to_csv( "dat/risk_return.csv" )
    #     display__risk_return( data=data )
    #     return( data )
    # df = multiple__analyze()
    
    data   = pd.read_csv( "dat/risk_return.csv" )

    for ik,sb in enumerate( sigma_bs ):
        df     = data[ data["sigma_b"] == sb ]
        xn,yn  = get__paretoFrontier( df=df )
        xe,ye  = find__elbowPoints( xn, yn )
        pareto = { "xn":xn, "yn":yn, "xe":xe, "ye":ye, "sigma_b":sb }
        pngFile = "png/Pmiss-EY__sb{:.01f}mm.png".format( sb )
        display__risk_return( data=df, pareto=pareto, pngFile=pngFile )

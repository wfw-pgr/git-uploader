import os, sys, json5
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ========================================================= #
# ===  plot__lattice                                    === #
# ========================================================= #

def plot__lattice( latticeFile=None, ax=None, height=1.0, y0=0.0, pngFile=None ):

    qf_plot = { "color":"royalblue", "alpha":0.8 }
    qd_plot = { "color":"tomato"   , "alpha":0.8 }
    rf_plot = { "color":"orange"   , "alpha":0.8 }
    dr_plot = { "color":"grey"     , "alpha":0.8 }
    
    # ------------------------------------------------- #
    # --- [1] load lattice file                     --- #
    # ------------------------------------------------- #
    with open( latticeFile, "r" ) as f:
        loaded   = json5.load( f )
        sequence = loaded["sequence"]
        elements = { seq:loaded["elements"][seq] for seq in sequence }
    lattice = pd.DataFrame.from_dict( elements, orient="index" )
    lattice = lattice[ [ "name", "type", "ds", "k" ] ]
    ds      = lattice.loc[ :,"ds" ].to_numpy()
    lattice["s_in"]  = np.cumsum( np.insert( ds, 0, 0.0 ) )[:-1]
    lattice["s_out"] = np.cumsum( ds )
    
    # ------------------------------------------------- #
    # --- [2] prepare figure / axis                 --- #
    # ------------------------------------------------- #
    if ( ax is None ):
        fig,ax   = plt.subplots( figsize=(8,2) )
        given_ax = False
    else:
        fig      = ax.figure
        given_ax = True

    # ------------------------------------------------- #
    # --- [3] draw lattice elements                 --- #
    # ------------------------------------------------- #
    for _, row in lattice.iterrows():
        s0,s1  = row["s_in"], row["s_out"]
        etype  = str( row["type"] ).lower()
        name   = str( row["name"] )
        width  = s1 - s0
        k      = row["k"]
        
        # -- [3-1] QF/QD -- #
        if   ( etype in ["quadrupole", "quadrupole.linear" ] ):
            if ( row["k"] > 0 ):
                ax.add_patch( patches.Rectangle( (s0,y0), width, height, **qf_plot ) )
            else:
                ax.add_patch( patches.Rectangle( (s0,y0-height), width, height, **qd_plot ) )
        # -- [3-2] RFcavity -- #
        elif ( etype in ["rfcavity", "rfgap" ] ):
            ax.add_patch( patches.Polygon( [ [s0,y0], [s1,y0+0.5*height], [s1,y0-0.5*height] ],
                                           closed=True, **rf_plot ) )
        # -- [3-3] drift  -- #
        elif ( etype in ["drift"] ):
            ax.plot( [s0,s1], [y0,y0], **drift_plot )
        # -- [3-4] その他（黒線） -- #
        else:
            ax.plot([s0, s1], [y0, y0], color="black", lw=1 )
            
        # --- ラベルを中央に配置 --- #
        if ( pngFile is None ):
            ax.text( (s0+s1)/2, y0+1.1*height*np.sign(y0+0.1),
                     name, ha="center", va="bottom", fontsize=7 )

    # ------------------------------------------------- #
    # --- [4] axis settings                         --- #
    # ------------------------------------------------- #
    if ( not( given_ax ) ):
        ax.set_xlim( lattice["s_in"].min(), lattice["s_out"].max() )
        ax.set_ylim( -1.5*height, 1.5*height )
        ax.set_xlabel("s [m]")
        ax.set_yticks([])
        ax.grid( False )

        legend_handles = [
            patches.Patch( color="royalblue", label="QF"),
            patches.Patch( color="tomato"   , label="QD"),
            patches.Patch( color="orange"   , label="RFcavity"),
            plt.Line2D([0], [0], color="gray", lw=2, label="Drift")
        ]
        plt.tight_layout()
        ax.legend( handles=legend_handles, loc="upper right", ncol=4, fontsize=6 )
        
        if ( pngFile is not None ):
            ax.axis( "off" )
            ax.set_facecolor("none")
            plt.savefig( pngFile, dpi=300 )
            plt.close()
        else:
            plt.show()

    return( lattice )

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    latticeFile = "dat/beamline_impactx.json"
    pngFile     = "lattice.png"
    plot__lattice( latticeFile=latticeFile, pngFile=pngFile )

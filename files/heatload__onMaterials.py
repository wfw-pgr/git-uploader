import meshio
import numpy  as np
import pandas as pd

# ========================================================= #
# ===  heatload__onMaterials.py                         === #
# ========================================================= #

def heatload__onMaterials( inpFile="heatload.csv", mshFile="rewrite_phits.bdf" ):

    mm           = 10.0
    
    rmesh        = meshio.read( mshFile )
    rheat        = pd.read_csv( inpFile )

    df            = pd.DataFrame( {} )
    df["x[mm]"]   = rheat["xCM[cm]"] * mm
    df["y[mm]"]   = rheat["yCM[cm]"] * mm
    df["z[mm]"]   = rheat["zCM[cm]"] * mm
    df["Q[W/m3]"] = rheat["Dose[J/m^3/source]"]
    df["matNum"]  = rmesh.cell_data_dict["nastran:ref"]["tetra"]

    matNumList    = list( set( df["matNum"].to_list() ) )

    for matNum in matNumList:
        outFile = "out/heatload_onMat_{:04}.csv".format( matNum )
        df_     = df[ df["matNum"] == matNum ]
        df_     = df_.drop( columns=["matNum"] )
        df_.to_csv( outFile, index=False )

    return( df )
        

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    heatload__onMaterials()

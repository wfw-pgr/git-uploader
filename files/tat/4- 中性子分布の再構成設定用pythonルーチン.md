# 線量の角度・エネルギー分布からのマルチソース設定

## コード (generate__beamDrivenNeutronSource.py)

```python
import numpy as np
import pandas as pd
import math


# ========================================================= #
# ===  generate__beamDrivenNeutronSource.py             === #
# ========================================================= #
def generate__beamDrivenNeutronSource( inpFile="dat/angle_energy_vs_neutrons.dat", surface="71", cut="72" ):

    s_section = """[source]
    totfact={totfact}"""
    s_format  = """
   <source>={weight}
   s-type=26
   suf={surface}
   cut={cut}
   proj=neutron
   dir=data
   a-type=11
   na=1
   {al} 1.0
   {ah}
   e-type=22
   ne={ne}
{values}
"""

    # .dat sample

    """
    al ah    el           eh      n[count/sr/MeV] r.err.
    0 10    1.0000E-10   1.0000E-09   0.0000E+00  0.0000
    0 10    1.0000E-09   1.0000E-08   0.0000E+00  0.0000
    0 10    1.0000E-08   1.0000E-07   2.6135E+14  0.7071
    ...... 
    """

    # ========================================================= #
    # ===  round__digit                                     === #
    # ========================================================= #
    def round__digit( x, digit=3 ):
        if ( ( x == 0 ) or ( x is None ) ):
            ret = 0
        else:
            ret = round( x, digit - int( math.floor( math.log10( abs( x ) ) ) ) - 1 )
        return( ret )

    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    data = pd.read_csv( inpFile, sep=r"\s+" )
    for col in [ "al", "ah", "el", "eh", "n[count/sr/MeV]" ]:
        data[col] = pd.to_numeric( data[col], errors="coerce" )

    # ------------------------------------------------- #
    # --- [2] bin yield                             --- #
    # ------------------------------------------------- #
    data["dE"]       = data["eh"] - data["el"]
    data["sr"]       = 2.0*np.pi*( np.cos(np.deg2rad(data["al"]) ) - \
                                   np.cos(np.deg2rad(data["ah"])) )
    data["n[count]"] = data["n[count/sr/MeV]"] * data["dE"] * data["sr"]

    # ------------------------------------------------- #
    # --- [3] group by angle                        --- #
    # ------------------------------------------------- #
    angleGroups = []
    for ( al, ah ), grp in data.groupby( [ "al", "ah" ], sort=True ):
        grp          = grp.sort_values( by=[ "el", "eh" ] ).copy()
        integ        = grp["n[count]"].sum()
        grp["eProb"] = 0.0 if ( integ <= 0.0 ) else grp["n[count]"] / integ

        angleGroups.append(
            {
                "al"    : float( al )   ,
                "ah"    : float( ah )   ,
                "yield" : float( integ ),
                "data"  : grp.copy(),
            }
        )
    totfact = sum( [ ag["yield"] for ag in angleGroups ] )

    # ------------------------------------------------- #
    # --- [4] make each <source>                    --- #
    # ------------------------------------------------- #
    sourceBlocks = []
    for ag in angleGroups:
        weight = 0.0 if totfact <= 0.0 else ag["yield"] / totfact
        
        eLines = []
        for _, row in ag["data"].iterrows():
            if ( row["eProb"] <= 0.0 ):
                continue
            eLines.append( "   {0} {1} {2}".format( round__digit( row["el"]    ),
                                                    round__digit( row["eh"]    ),
                                                    round__digit( row['eProb'], digit=8 ) ) )
        values = "\n".join( eLines )
        ne     = len( eLines )

        sourceBlocks.append(
            s_format.format(
                weight  = round__digit( weight, digit=8 ), 
                surface = surface,
                cut     = cut, 
                al      = round__digit( ag["al"] ), 
                ah      = round__digit( ag["ah"] ),
                ne      = ne, 
                values  = values,
            )
        )

    # ------------------------------------------------- #
    # --- [5] return                                 -- #
    # ------------------------------------------------- #
    text = s_section.format( totfact=totfact ) + "\n" + "".join( sourceBlocks )
    return( text )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    ret     = generate__beamDrivenNeutronSource()
    outFile = "dat/source_n_phits.inp"
    
    with open( outFile, "w" ) as f:
        f.write( ret )

```

## 出力サンプル (source_n_phits.inp)

```
[source]
    totfact=460936426990.3336

   <source>=0.020093855
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   0 1.0
   10.0
   e-type=22
   ne=10
   1e-08 1e-07 0.00024241674
   1e-07 1e-06 0.00014184185
   1e-06 1e-05 0.00094545774
   1e-05 0.0001 0.0027945404
   0.0001 0.001 0.0093330675
   0.001 0.01 0.0265921
   0.01 0.1 0.093015306
   0.1 1.0 0.53157302
   1.0 10.0 0.33450449
   10.0 100.0 0.0008577666

   <source>=0.059425494
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   10.0 1.0
   20.0
   e-type=22
   ne=10
   1e-08 1e-07 5.8371037e-05
   1e-07 1e-06 0.0003507329
   1e-06 1e-05 0.001152593
   1e-05 0.0001 0.0022325378
   0.0001 0.001 0.0090829919
   0.001 0.01 0.026960897
   0.01 0.1 0.092356465
   0.1 1.0 0.54427539
   1.0 10.0 0.32257703
   10.0 100.0 0.00095299652

   <source>=0.097136247
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   20.0 1.0
   30.0
   e-type=22
   ne=10
   1e-08 1e-07 8.1493667e-05
   1e-07 1e-06 0.00028897599
   1e-06 1e-05 0.00096548628
   1e-05 0.0001 0.0026245
   0.0001 0.001 0.008642763
   0.001 0.01 0.026994911
   0.01 0.1 0.092650211
   0.1 1.0 0.5362231
   1.0 10.0 0.33056531
   10.0 100.0 0.0009632533

   <source>=0.13113917
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   30.0 1.0
   40.0
   e-type=22
   ne=9
   1e-08 1e-07 9.7209147e-05
   1e-07 1e-06 0.00028683854
   1e-06 1e-05 0.00082493555
   1e-05 0.0001 0.0021414446
   0.0001 0.001 0.0072535066
   0.001 0.01 0.025773098
   0.01 0.1 0.089778863
   0.1 1.0 0.54408314
   1.0 10.0 0.32976096

   <source>=0.1568131
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   40.0 1.0
   50.0
   e-type=22
   ne=10
   1e-08 1e-07 7.6829257e-05
   1e-07 1e-06 0.00024121845
   1e-06 1e-05 0.00051665009
   1e-05 0.0001 0.0020741026
   0.0001 0.001 0.0067659773
   0.001 0.01 0.02302062
   0.01 0.1 0.085753809
   0.1 1.0 0.54904076
   1.0 10.0 0.33163077
   10.0 100.0 0.00087926366

   <source>=0.17414962
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   50.0 1.0
   60.0
   e-type=22
   ne=10
   1e-08 1e-07 3.2588739e-05
   1e-07 1e-06 0.00025986094
   1e-06 1e-05 0.00067792785
   1e-05 0.0001 0.0021250376
   0.0001 0.001 0.0062762342
   0.001 0.01 0.020925475
   0.01 0.1 0.08031407
   0.1 1.0 0.55051209
   1.0 10.0 0.33777698
   10.0 100.0 0.0010997367

   <source>=0.1746281
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   60.0 1.0
   70.0
   e-type=22
   ne=11
   1e-09 1e-08 1.3834428e-05
   1e-08 1e-07 2.0176179e-05
   1e-07 1e-06 0.00010229486
   1e-06 1e-05 0.00044896132
   1e-05 0.0001 0.0016506975
   0.0001 0.001 0.0057617369
   0.001 0.01 0.017772218
   0.01 0.1 0.072203173
   0.1 1.0 0.54678454
   1.0 10.0 0.35409033
   10.0 100.0 0.0011520366

   <source>=0.1429112
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   70.0 1.0
   80.0
   e-type=22
   ne=10
   1e-08 1e-07 4.818639e-05
   1e-07 1e-06 0.00016269302
   1e-06 1e-05 0.00045950373
   1e-05 0.0001 0.0013974024
   0.0001 0.001 0.0044487639
   0.001 0.01 0.014446811
   0.01 0.1 0.059668563
   0.1 1.0 0.53305959
   1.0 10.0 0.38484937
   10.0 100.0 0.0014591205

   <source>=0.043703206
   s-type=26
   suf=71
   cut=72
   proj=neutron
   dir=data
   a-type=11
   na=1
   80.0 1.0
   90.0
   e-type=22
   ne=9
   1e-07 1e-06 0.00021431632
   1e-06 1e-05 0.00020704342
   1e-05 0.0001 0.00096970261
   0.0001 0.001 0.002835599
   0.001 0.01 0.012840163
   0.01 0.1 0.052211756
   0.1 1.0 0.49818331
   1.0 10.0 0.43107968
   10.0 100.0 0.0014584292

```


## PHITS記載上の注意点

> [!note]  
> # PHITS  (`e-type=22` と `a-type=11` ) の入力形式について
> 
> - マルチソース記載時に要注意
> - `e-type=22` ： `ne` 個の区間に対しne 行の`el eh weight` を書く。 
> (e.g.)   
> ```
>  e-type=22
>  ne=3
>  0 1 0.1
>  1 2 0.2
>  2 3 0.7
> ```
> 
> - `a-type=11` ： `na` 個の区間に対しna行の`ang weight`を書き、na+1行目に最終angを１行記載
> (e.g.)   
> ```
>  a-type=11
>  na=2
>  0 0.2
>  10 0.8
>  20        $$ << 最終角度
> ```
> 
> 


# マルチソース設定の動作確認

## 上記 マルチソース自動生成コードの動作について

- コードの動作自体は確認
- ソース記述を電子と中性子で分けた
	- source_e_phits.inp
	- source_n_phits.inp

## 動作検証用にタリーを追加

- タリーは２段構成
	- ソースイミテーション用　（前段）
	- 中性子評価用　（後段）

- 検証用タリー想定図

![[IMG_3302.jpg|553]]


## 今後の流れ

 1. 正しい中性子フラックスが再構成ソースから得られることを確認する
 2. 中性子による製造量評価コードの作成
 3. 固体系の計算
 4. 液体系の計算
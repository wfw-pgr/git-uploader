# PHITS体系の作成

- 中性子フラックス再構成の体型 + Raターゲット体系
  
 ![[IMG_3303.jpg|458]]



# 中性子捕獲計算用の体系

## ターゲット部分のジオメトリへの追加

- 生成したジオメトリは下記
- 変更点
	- タリー領域は、R50mm はでかすぎるため、D=10mmに変更
		- ほぼ中心に集まっている粒子源が、薄く伸ばされてしまうため。
		- 程度問題だが、これでも同種の問題はまだ残っている。
		- 再計算必要
	- ターゲット径はD=10mmを採用
	- 中性子ソースと検証用の仮想タリー円筒について、厚みを0.5mmへ
		- 厚みは何でもいい。（どこで測るか、物理的意味はない）
		- 単にガラス管と干渉していたから縮めた。

![[Ac225ng_geometry.png]]


## ジオメトリ設定後の粒子輸送計算の動作を確認

- 製造量計算用のタリーについては、いつものfluenceを設定

# PHITS体系（コード）

## main_phits.inp
```python
$$
$$ ================================================================ $$
$$ ===  PHITS input file   ( main_phits.inp )                   === $$
$$ ================================================================ $$
$$

$$ ---   [NOTE]    --------------------------------------------------------------  $$
$$ *                                                                            *  $$
$$ * ( space >= 6 ): continuing line  (Error might occur with too many space.)  *  $$
$$ *                                                                            *  $$
$$ ------------------------------------------------------------------------------  $$

$ <loadJSON> filepath = "inp/parameters.json"

$$ ---   [Parallelization]    ---------------------------------------------------  $$
$$ -- use $MPI=... / $OMP=...  -- $$
@sim.parallel.cmd
$$ ------------------------------------------------------------------------------  $$

$$ $ <include> filepath = inp/variables.def

[Title]
input file for radiation shieldings.

[Parameters]
  icntl     = @sim.icntl               $$ ( 0:transport, 6:check-source, 8:check-Geometry )
  istdev    = @sim.istdev              $$ ( 0:optimal  , 1:batch-stddev, 2:history-stddev ) ( +:New, -:Continue )
  file(1)   = @sim.phits_directory     $$
  file(6)   = @sim.phits_output        $$ File Name of output
  file(7)   = @sim.phits_xsdir         $$ directory path of xsdir
  maxcas    = @sim.nCascade            $$ #.of particles
  maxbch    = @sim.nBatch              $$ #.of batches
  emin(12)  = 0.1                      $$ cut-off energy of electron to be transported. (MeV)
                                       $$   ( if negs=1 ) Default :: 0.1 = 100keV
                                       $$   ( if negs=0 ) Default :: 1e9 :: No e- transport
                                       $$ if emin(12) is set, the value is prioritized.
  emin(13)  = 0.1                      $$ cut-off energy of electron to be transported.
  negs      = 1                        $$ transport of photon (+1/-1), electron(+1), off(0)
  ipnint    = 1                        $$ p-n interaction ( 0:Off, 1:On, 2:w/ NRF(Full) )
  iprofr    = 0                        $$ error - handling ( exceeding desk device )
  itimrand  = 1                        $$ randomize by date-time ( random seed varies, run by run. )

$ <include> filepath = inp/source_e_phits.inp
$$ $ <include> filepath = inp/source_n_phits.inp
$ <include> filepath = inp/geometry_phits.inp
$ <include> filepath = inp/materials_phits.inp
$ <include> filepath = inp/tally__cross_phits.inp
$ <include> filepath = inp/tally__fluence_phits.inp
$$ $ <include> filepath = inp/tally__checkGeometry_phits.inp



[End]

$ <postProcess> for f in `ls out/*.eps`; do gs -dSAFER -dEPSCrop -sDEVICE=pdfwrite -o ${f%.eps}_%d.pdf ${f}; done
$ <postProcess> mogrify -background white -alpha off -density 400 -resize 50%x50% -path png -format png out/*.pdf



$$ ---   [NOTE]    --------------------------------------------------------------  $$
$$ nucdata   =  1                       $$ nuetron's nuclear data library => 0:Off, 1:On
$$ negs      =  1                       $$ transports of electron, photon, position ( default:-1 )
                                        $$  -1: PHITS's original library ( photon )
                                        $$   0: No Transport
                                        $$  +1: EGS5 Library             ( photon, electron )
$$ emcpf     = 20.0                     $$ upper limit of the detailed photon model
$$ emin(12)  = 0.1     $ ==  1(keV)     $$ upr-limit of transport :: electron (MeV)
$$ emin(13)  = 0.1     $ ==  1(keV)     $$ upr-limit of transport :: positron (MeV)
$$ dmax(12)  = 1000.0                   $$ use of nuclear data ( emin(12) < energy < dmax(12) )
$$ ------------------------------------------------------------------------------  $$

```
## parameters.json

```json
{
    
    // ---------------------------------------------- //
    // ---  Simulation Control Settings          ---- //
    // ---------------------------------------------- //
    //
    "sim.icntl"          :     0,    // ( 0:transport, 6:check-source, 8:check-Geometry )
    "sim.istdev"         :     2,    // ( 0:optimal  , 1:batch-stddev, 2:history-stddev ) ( +:New, -:Continue )
    "sim.nParallel"      :    55,
    "sim.nParticle"      : 1.1e9,
    "sim.nBatch"         : "@sim.nParallel *50",
    "sim.nCascade"       : "@sim.nParticle/@sim.nBatch",
    "sim.parallel.cmd"   : "'$MPI = @sim.nParallel'",
    "sim.phits_output"   : "out/phits.out",

    // --- level7 & galleria --- //    ( 133.144.160.74 & 133.144.160.131 )
    // "sim.phits_directory": "/mnt/c/phits/build_phits328A/phits/",
    // "sim.phits_xsdir"    : "/mnt/c/phits/build_phits328A/phits/data/xsdir.jnd",
    // ---      z840         --- //    ( 133.144.160.159 )
    // "sim.phits_directory" : "/mnt/e/nishida/phits/build/phits/",     
    // "sim.phits_xsdir"    : "/home/users/70727338/Lib80x/xsdir.jnd",
    // ---     rdhpc1        --- //    ( 10.225.216.10   )
    "sim.phits_directory": "/common1/hpclocal/PHITS/phits321/phits/",
    "sim.phits_xsdir"    : "/home/users/70727338/Lib80x/xsdir.jnd",
            
    // ---------------------------------------------- //
    // ---  target Settings                      ---- //
    // ---------------------------------------------- //
    "target.distance"    : "6.0  * @mm",
    "target.diameter"    : "10.0  * @mm",
    "target.offset.x"    : "0.0  * @mm",
    "target.density"     : "@RaCl2.density",
    "target.matNum"      : "@RaCl2.matNum" ,
    "target.radius"      : "0.5  * @target.diameter",
    "target.Area"        : "0.25 * @pi * ( @target.diameter )*( @target.diameter )",

    // -- for non-RI -- //
    // "target.mass"        : 5.0e-3,                                                     // -- [g]  -- //
    // "target.thick"       : "@target.mass / ( abs( @target.density ) * @target.Area )", // -- [cm] -- //

    // -- for RI     -- // 
    "target.activity"    :  11.1e9,                       // -- [Bq]    --- //
    "target.halflife"    : "1600.0*365.0*24.0*3600",      // -- [s]     --- //
    "target.g_mol"       : 297.0,                         // -- [g/mol] --- //
    "target.QTM"         : "@target.activity * @target.halflife * @target.g_mol",
    "target.thick"       : "@target.QTM / ( @ln2 * @NAvogadro * abs( @target.density ) * @target.Area )",

    
    // ---------------------------------------------- //
    // ---  convertor Settings                   ---- //
    // ---------------------------------------------- //
    "converter.thick"    : "1.0  * @mm" ,
    "converter.matNum"   : "@Ta.matNum" ,
    "converter.density"  : "@Ta.density",

    
    // ---------------------------------------------- //
    // ---  quartz Tube  Settings                ---- //
    // ---------------------------------------------- //
    "qTube.thick"        : "1.0  * @mm",
    "qTube.length1"      : "20.0 * @mm",
    "qTube.length2"      : "53.0 * @mm",
    "qTube.length"       : "@qTube.length1 + @qTube.length2",
    
    "qTube.diameter1"    :  "@target.diameter + 2.0*@qTube.thick",
    "qTube.diameter2"    : "11.0 * @mm",
    "qTube.radius1"      :  "0.5 * @qTube.diameter1",
    "qTube.radius2"      :  "0.5 * @qTube.diameter2",
    "qTube.z.maxLen"     :  "@qTube.length1",

    
    // ---------------------------------------------- //
    // ---  source part  :: beam settings        ---- //
    // ---------------------------------------------- //
    "beam.energy"        :     40.0,
    "beam.current"       : 100.0e-6,
    "beam.FWHM"          : "6.00* @mm",
    "beam.zStart"        : "-200.0 * @mm",
    "beam.length"        : "  10.0 * @mm",

    "beam.totfact"       : "@beam.current / 1.602e-19",              // -- unit :: [ particles / s ] -- //
    "beam.HWHM"          : "0.5 * @beam.FWHM",
    "beam.zEnd"          : "@beam.zStart - @beam.length",

    
    // ---------------------------------------------- //
    // ---  Constants  Settings                  ---- //
    // ---------------------------------------------- //    
    "mm"                 : 0.1,
    "m2cm"               : 100.0,
    "pi"                 : 3.14159265358,
    "ln2"                : 0.69314718056,
    "NAvogadro"          : 6.02e23,

    
    // ---------------------------------------------- //
    // ---  Geometry part                        ---- //
    // ---------------------------------------------- //
    // --------------------------- //
    // -- convertor             -- //
    // --------------------------- //
    "lyr.Lx"             : "300.0 * @mm",
    "lyr.Ly"             : "300.0 * @mm",
    "lyr.Ti.thick"       : "0.05 * @mm",
    "lyr.He.thick"       : "14.0 * @mm",
    "lyr.H2O.thick"      : "1.5  * @mm",
    "lyr.SUS316.thick"   : "0.5  * @mm",
    "lyr.Housing.thick"  : "0.1  * @mm",
    "lyr.airgap1.thick"  : "38.3 * @mm",
    "lyr.airgap2.thick"  : "0.5  * @mm",
    "lyr.airgap3.thick"  : "@target.distance + 1.2*@qTube.z.maxLen",
    
    "lyr.xMin"           : "(-0.5) * @lyr.Lx",
    "lyr.xMax"           : "(+0.5) * @lyr.Lx",
    "lyr.yMin"           : "(-0.5) * @lyr.Ly",
    "lyr.yMax"           : "(+0.5) * @lyr.Ly",
    "lyr.zstart"         : "-1.0*( 2.0*@lyr.Ti.thick + @lyr.He.thick + @lyr.airgap1.thick + 1.0*@lyr.SUS316.thick + 3.0*@converter.thick + 3.0*@lyr.H2O.thick )",

    // -- [01]  Ti   0.05 mm   -- //
    "lyr.01.zMin"        : "@lyr.zstart",
    "lyr.01.zMax"        : "@lyr.01.zMin + @lyr.Ti.thick",
    // -- [02]  He     14 mm   -- //
    "lyr.02.zMin"        : "@lyr.01.zMax",
    "lyr.02.zMax"        : "@lyr.02.zMin + @lyr.He.thick",
    // -- [03]  Ti   0.05 mm   -- //
    "lyr.03.zMin"        : "@lyr.02.zMax",
    "lyr.03.zMax"        : "@lyr.03.zMin + @lyr.Ti.thick",
    // -- [04]  Air  38.3 mm   -- //
    "lyr.04.zMin"        : "@lyr.03.zMax",
    "lyr.04.zMax"        : "@lyr.04.zMin + @lyr.airgap1.thick",
    // -- [05]  SUS316 0.5 mm  -- //
    "lyr.05.zMin"        : "@lyr.04.zMax",
    "lyr.05.zMax"        : "@lyr.05.zMin + @lyr.SUS316.thick",
    // -- [06]  H2O    1.5 mm  -- //
    "lyr.06.zMin"        : "@lyr.05.zMax",
    "lyr.06.zMax"        : "@lyr.06.zMin + @lyr.H2O.thick",
    // -- [07] converter(1) 1.0 mm  -- //
    "lyr.07.zMin"        : "@lyr.06.zMax",
    "lyr.07.zMax"        : "@lyr.07.zMin + @converter.thick",
    // -- [08]  H2O    1.5 mm  -- //
    "lyr.08.zMin"        : "@lyr.07.zMax",
    "lyr.08.zMax"        : "@lyr.08.zMin + @lyr.H2O.thick",
    // -- [09] converter(2) 1.0 mm  -- //
    "lyr.09.zMin"        : "@lyr.08.zMax",
    "lyr.09.zMax"        : "@lyr.09.zMin + @converter.thick",
    // -- [10]  H2O    1.5 mm  -- //
    "lyr.10.zMin"        : "@lyr.09.zMax",
    "lyr.10.zMax"        : "@lyr.10.zMin + @lyr.H2O.thick",
    // -- [11] converter(3) 1.0 mm  -- //
    "lyr.11.zMin"        : "@lyr.10.zMax",
    "lyr.11.zMax"        : "@lyr.11.zMin + @converter.thick",
    // -- [12]  H2O    1.5 mm  -- //
    "lyr.12.zMin"        : "@lyr.11.zMax",
    "lyr.12.zMax"        : "@lyr.12.zMin + @lyr.H2O.thick",
    // -- [13]  SUS316 0.5 mm  -- //
    "lyr.13.zMin"        : "@lyr.12.zMax",
    "lyr.13.zMax"        : "@lyr.13.zMin + @lyr.SUS316.thick",
    // -- [14]  air      3.0 mm  -- //
    "lyr.14.zMin"        : "@lyr.13.zMax",
    "lyr.14.zMax"        : "@lyr.14.zMin + @lyr.airgap2.thick",
    // -- [15]  SUS316   0.1 mm  -- //
    "lyr.15.zMin"        : "@lyr.14.zMax",
    "lyr.15.zMax"        : "@lyr.15.zMin + @lyr.Housing.thick",
    // -- [16]  air      xxx mm  -- //
    "lyr.16.zMin"        : "@lyr.15.zMax",
    "lyr.16.zMax"        : "@lyr.16.zMin + @lyr.airgap3.thick",
    

    // --------------------------- //
    // -- tally cylinder        -- //
    // --------------------------- //
    "tally.z.length"     : "0.5 * @mm",
    "tally.diameter"     : "10.0 * @mm",
    
    "tally.radius"       : "0.5*@tally.diameter",
    
    "tally.x0.01"        : 0.0, 
    "tally.y0.01"        : 0.0, 
    "tally.z0.01"        : "@lyr.16.zMin",
    "tally.dx.01"        : 0.0, 
    "tally.dy.01"        : 0.0, 
    "tally.dz.01"        : "@tally.z.length",

    "tally.x0.02"        : 0.0, 
    "tally.y0.02"        : 0.0, 
    "tally.z0.02"        : "@tally.z0.01 + @tally.dz.01",
    "tally.dx.02"        : 0.0, 
    "tally.dy.02"        : 0.0, 
    "tally.dz.02"        : "@tally.z.length",

    "tally.x0.03"        : 0.0, 
    "tally.y0.03"        : 0.0, 
    "tally.z0.03"        : "@tally.z0.02 + @tally.dz.02",
    "tally.dx.03"        : 0.0, 
    "tally.dy.03"        : 0.0, 
    "tally.dz.03"        : "@tally.z.length",

    // --------------------------- //
    // -- quart tube            -- //
    // --------------------------- //
    "qTube.x0.01"        : "@target.offset.x", 
    "qTube.y0.01"        : 0.0, 
    "qTube.z0.01"        : "@target.distance - @qTube.thick", 
    "qTube.dx.01"        : 0.0, 
    "qTube.dy.01"        : 0.0, 
    "qTube.dz.01"        : "@qTube.length1",

    "qAir.radius1"       : "@qTube.radius1 - @qTube.thick",
    "qAir.length1"       : "@qTube.length1 - @qTube.thick*2",

    "qAir.x0.01"         : "@target.offset.x",
    "qAir.y0.01"         : 0.0,
    "qAir.z0.01"         : "@target.distance",
    "qAir.dx.01"         : 0.0,
    "qAir.dy.01"         : 0.0,
    "qAir.dz.01"         : "@qAir.length1",

    // --------------------------- //
    // -- target                -- //
    // --------------------------- //
    "target.x0"          : "@target.offset.x",
    "target.y0"          : 0.0,
    "target.z0"          : "@target.distance",
    "target.dx"          : 0.0, 
    "target.dy"          : 0.0,
    "target.dz"          : "@target.thick",

    // --------------------------- //
    // -- buffer air            -- //
    // --------------------------- //
    "buff.margin"        : "50.0 * @mm",
    "buff.xMin"          : "@lyr.xMin    - @buff.margin",
    "buff.xMax"          : "@lyr.xMax    + @buff.margin",
    "buff.yMin"          : "@lyr.yMin    - @buff.margin",
    "buff.yMax"          : "@lyr.xMax    + @buff.margin",
    "buff.zMin"          : "@lyr.01.zMin - @buff.margin",
    "buff.zMax"          : "@lyr.16.zMax + @buff.margin",

    // ---------------------------------------------- //
    // ---  Bounding Box part                    ---- //
    // ---------------------------------------------- //
    "bb.xMin"            : "-500.0 * @mm",
    "bb.xMax"            : "+500.0 * @mm",
    "bb.yMin"            : "-500.0 * @mm",
    "bb.yMax"            : "+500.0 * @mm",
    "bb.zMin"            : "-500.0 * @mm",
    "bb.zMax"            : "+500.0 * @mm",
        
}

```

## source_e_phits.inp

```python

$$ ================================================================= $$
$$ ===  source                                                   === $$
$$ ================================================================= $$

[Source]

    $$ ----------------------------------------------------------------- $$
    $$ ---             pencil beam ( cylinder shape )                --- $$
    $$ ----------------------------------------------------------------- $$
    $$ s-type    =    1                    $$ ( 1:cylinder( pencil beam ) )
    $$ totfact   = @beam.totfact
    $$ proj      = electron
    $$ dir       =  1.0
    $$ r0        = @beam.HWHM
    $$ z0        = @beam.zStart
    $$ z1        = @beam.zEnd
    $$ e0        = @beam.energy


    $$ ----------------------------------------------------------------- $$
    $$ ---         Gaussian beam ( Gaussian distribution )           --- $$
    $$ ----------------------------------------------------------------- $$
    s-type    =   13                    $$ ( 13:gaussian-xy )
    totfact   = @beam.totfact
    proj      = electron
    dir       =  1.0
    r1        = @beam.FWHM
    z0        = @beam.zStart
    z1        = @beam.zEnd
    e0        = @beam.energy


    $$ ----------------------------------------------------------------- $$
    $$ ---         Beam profile ( beam emittance )                   --- $$
    $$ ----------------------------------------------------------------- $$
    $$ s-type    =   11                    $$ ( 11: beam-profile-xy )
    $$ totfact   = @beam.totfact
    $$ proj      = electron
    $$ dir       =  1.0
    $$ z0        = @beam.zStart
    $$ z1        = @beam.zEnd
    $$ rx        = 0.0
    $$ ry        = 0.0
    $$ wem       = 0.0
    $$ x1        = @beam.HWHM
    $$ y1        = @beam.HWHM
    $$ xmrad1    = 0.0
    $$ ymrad1    = 0.0
    $$ x2        = 0.0    
    $$ y2        = 0.0    
    $$ xmrad2    = 0.0
    $$ ymrad2    = 0.0
    $$ e0        = @beam.energy

```

## source_n_phits.inp

```python
[source]
    totfact=461690127426.8655

   <source>=0.019795935
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   0 1.0
   10.0
   e-type=22
   ne=10
   1e-08 1e-07 6.2607248e-05
   1e-07 1e-06 0.00040219787
   1e-06 1e-05 0.00060327801
   1e-05 0.0001 0.0026930375
   0.0001 0.001 0.0084207007
   0.001 0.01 0.028220965
   0.01 0.1 0.091102687
   0.1 1.0 0.54227342
   1.0 10.0 0.32535465
   10.0 100.0 0.0008664531

   <source>=0.059328638
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   10.0 1.0
   20.0
   e-type=22
   ne=10
   1e-08 1e-07 8.1687198e-05
   1e-07 1e-06 0.0001748025
   1e-06 1e-05 0.00070782532
   1e-05 0.0001 0.0024433046
   0.0001 0.001 0.008572103
   0.001 0.01 0.02621013
   0.01 0.1 0.095047928
   0.1 1.0 0.53480177
   1.0 10.0 0.33078169
   10.0 100.0 0.001178762

   <source>=0.097011367
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   20.0 1.0
   30.0
   e-type=22
   ne=11
   1e-09 1e-08 4.4676714e-06
   1e-08 1e-07 8.0483191e-05
   1e-07 1e-06 0.00033235718
   1e-06 1e-05 0.00072486306
   1e-05 0.0001 0.0026573507
   0.0001 0.001 0.0078438861
   0.001 0.01 0.025672253
   0.01 0.1 0.093427208
   0.1 1.0 0.53950608
   1.0 10.0 0.32883215
   10.0 100.0 0.00091889775

   <source>=0.13079272
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   30.0 1.0
   40.0
   e-type=22
   ne=9
   1e-08 1e-07 6.3490989e-05
   1e-07 1e-06 0.00024462176
   1e-06 1e-05 0.00066493638
   1e-05 0.0001 0.0021358409
   0.0001 0.001 0.0073550377
   0.001 0.01 0.024480902
   0.01 0.1 0.089615061
   0.1 1.0 0.54493343
   1.0 10.0 0.33050668

   <source>=0.15808567
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   40.0 1.0
   50.0
   e-type=22
   ne=10
   1e-08 1e-07 7.9182395e-05
   1e-07 1e-06 0.00019694372
   1e-06 1e-05 0.00060870822
   1e-05 0.0001 0.0023827487
   0.0001 0.001 0.0070448228
   0.001 0.01 0.023499932
   0.01 0.1 0.084592307
   0.1 1.0 0.54846863
   1.0 10.0 0.33203395
   10.0 100.0 0.0010927736

   <source>=0.17476432
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   50.0 1.0
   60.0
   e-type=22
   ne=11
   1e-09 1e-08 3.7647824e-06
   1e-08 1e-07 8.5770112e-05
   1e-07 1e-06 0.00022753212
   1e-06 1e-05 0.00051404626
   1e-05 0.0001 0.0018261011
   0.0001 0.001 0.0063758428
   0.001 0.01 0.021217117
   0.01 0.1 0.080993709
   0.1 1.0 0.54640932
   1.0 10.0 0.34139325
   10.0 100.0 0.00095354941

   <source>=0.17458857
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   60.0 1.0
   70.0
   e-type=22
   ne=11
   1e-09 1e-08 6.9856209e-06
   1e-08 1e-07 5.8107111e-05
   1e-07 1e-06 0.00018170594
   1e-06 1e-05 0.0005104945
   1e-05 0.0001 0.0016515901
   0.0001 0.001 0.0055344116
   0.001 0.01 0.017319419
   0.01 0.1 0.071638357
   0.1 1.0 0.54559439
   1.0 10.0 0.35639634
   10.0 100.0 0.0011082012

   <source>=0.14275536
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   70.0 1.0
   80.0
   e-type=22
   ne=10
   1e-08 1e-07 4.3069458e-05
   1e-07 1e-06 0.00016445385
   1e-06 1e-05 0.00046584182
   1e-05 0.0001 0.0013056919
   0.0001 0.001 0.004597167
   0.001 0.01 0.013864887
   0.01 0.1 0.06005657
   0.1 1.0 0.53021343
   1.0 10.0 0.38799205
   10.0 100.0 0.0012968365

   <source>=0.042877434
   s-type=26
   suf=74
   cut=-75
   proj=neutron
   dir=data
   a-type=11
   na=1
   80.0 1.0
   90.0
   e-type=22
   ne=10
   1e-08 1e-07 2.3603875e-05
   1e-07 1e-06 0.000181698
   1e-06 1e-05 0.00022692657
   1e-05 0.0001 0.0012056652
   0.0001 0.001 0.0041644705
   0.001 0.01 0.012328976
   0.01 0.1 0.051354611
   0.1 1.0 0.50005393
   1.0 10.0 0.42931919
   10.0 100.0 0.0011409325

```

## geometry_phits.inp

```python

$$ ========================================================== $$
$$ ===       geometry_phits.inp                           === $$
$$ ========================================================== $$
$$
[Surface]

   $$ ------------------------------------------- $$
   $$ --- [1] target system                    -- $$
   $$ ------------------------------------------- $$
   $$ [surfNum] [rpp] [xMin] [xMax] [yMin] [yMax] [zMin] [zMax]  -- $
   21  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.01.zMin @lyr.01.zMax
   22  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.02.zMin @lyr.02.zMax
   23  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.03.zMin @lyr.03.zMax
   24  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.04.zMin @lyr.04.zMax
   25  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.05.zMin @lyr.05.zMax
   26  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.06.zMin @lyr.06.zMax
   27  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.07.zMin @lyr.07.zMax
   28  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.08.zMin @lyr.08.zMax
   29  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.09.zMin @lyr.09.zMax
   30  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.10.zMin @lyr.10.zMax
   31  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.11.zMin @lyr.11.zMax
   32  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.12.zMin @lyr.12.zMax
   33  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.13.zMin @lyr.13.zMax
   34  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.14.zMin @lyr.14.zMax
   35  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.15.zMin @lyr.15.zMax
   36  rpp  @lyr.xMin @lyr.xMax @lyr.yMin @lyr.yMax @lyr.16.zMin @lyr.16.zMax
   
   $$ ------------------------------------------- $$
   $$ --- [2] irradiation target               -- $$
   $$ ------------------------------------------- $$
   $$ [surfNum] [rcc] [x0] [y0] [z0] [dx] [dy] [dz] [r0] -- $
   41  rcc  @qTube.x0.01 @qTube.y0.01 @qTube.z0.01 @qTube.dx.01 @qTube.dy.01 @qTube.dz.01 @qTube.radius1
   43  rcc  @qAir.x0.01  @qAir.y0.01  @qAir.z0.01  @qAir.dx.01  @qAir.dy.01  @qAir.dz.01  @qAir.radius1
   45  rcc  @target.x0   @target.y0   @target.z0   @target.dx   @target.dy   @target.dz   @target.radius
   

   $$ ------------------------------------------- $$
   $$ --- [3] background air / boundary void   -- $$
   $$ ------------------------------------------- $$
   $$  --  background air     -- $$
   $$ [surfNum] [rpp] [xMin] [xMax] [yMin] [yMax] [zMin] [zMax]  -- $
   51  rpp     @buff.xMin @buff.xMax @buff.yMin @buff.yMax @buff.zMin @buff.zMax
   
   $$ -- boundary void region -- $$
   $$ [surfNum] [rpp] [xMin] [xMax] [yMin] [yMax] [zMin] [zMax]  -- $
   61  rpp     @bb.xMin @bb.xMax @bb.yMin @bb.yMax @bb.zMin @bb.zMax

   $$ ------------------------------------------- $$
   $$ --- [4] neutron settings                 -- $$
   $$ ------------------------------------------- $$
   71  rcc  @tally.x0.01 @tally.y0.01 @tally.z0.01 @tally.dx.01 @tally.dy.01 @tally.dz.01 @tally.radius
   72  rcc  @tally.x0.02 @tally.y0.02 @tally.z0.02 @tally.dx.02 @tally.dy.02 @tally.dz.02 @tally.radius
   73  rcc  @tally.x0.03 @tally.y0.03 @tally.z0.03 @tally.dx.03 @tally.dy.03 @tally.dz.03 @tally.radius

   74  PZ  @tally.z0.02
   75  CZ  @tally.radius

   $$ ------------------------------------------- $$
   $$ --- [x] template of surface geometry     -- $$
   $$ ------------------------------------------- $$
   $$ [surfNum] [rpp] [xMin] [xMax] [yMin] [yMax] [zMin] [zMax]  -- $
   $$ [surfNum] [rcc] [x0] [y0] [z0] [dx] [dy] [dz] [r0]         -- $


[Cell]

   $$ ------------------------------------------- $$
   $$ --- [1] target system                    -- $$
   $$ ------------------------------------------- $$
   
   $$ [cellNum]  [matNum] [Density]          [surfNums]
   321 @Ti.matNum         @Ti.density        -21
   322 @He.matNum         @He.density        -22
   323 @Ti.matNum         @Ti.density        -23
   324 @Air.matNum        @Air.density       -24
   325 @SUS316.matNum     @SUS316.density    -25
   326 @H2O.matNum        @H2O.density       -26
   327 @converter.matNum  @converter.density -27
   328 @H2O.matNum        @H2O.density       -28
   329 @converter.matNum  @converter.density -29
   330 @H2O.matNum        @H2O.density       -30
   331 @converter.matNum  @converter.density -31
   332 @H2O.matNum        @H2O.density       -32
   333 @SUS316.matNum     @SUS316.density    -33
   334 @Air.matNum        @Air.density       -34
   335 @SUS316.matNum     @SUS316.density    -35
   336 @Air.matNum        @Air.density       -36 +41 +71 +72 +73 

   $$ ------------------------------------------- $$
   $$ --- [2] irradiation target               -- $$
   $$ ------------------------------------------- $$
   341 @SiO2.matNum       @SiO2.density      -41 +43
   343 @Air.matNum        @Air.density       -43 +45
   345 @target.matNum     @target.density    -45

   $$ ------------------------------------------- $$
   $$ --- [3] background air / boundary void   -- $$
   $$ ------------------------------------------- $$
   351 @Air.matNum        @Air.density       -51 +21 +22 +23 +24 +25 +26 +27 +28 +29
                                             +30 +31 +32 +33 +34 +35 +36
   361 @Air.matNum	      @Air.density       -61 +51
   301 -1                                    +61

   $$ ------------------------------------------- $$
   $$ --- [4] neutron tally                    -- $$
   $$ ------------------------------------------- $$
   371 @Air.matNum        @Air.density       -71
   372 @Air.matNum        @Air.density       -72
   373 @Air.matNum        @Air.density       -73


   $$ ------------------------------------------- $$
   $$ --- [x] template of surface geometry     -- $$
   $$ ------------------------------------------- $$
   $$ [cellNum]   [matNum] [density]  [surfNums]  #<cellNum>      <- NOT operator !!
   $$ [cellNum]   [matNum] [density]  [surfNums]  #(<surfNum>)    <- USE () for surface num.
   $$ [surfNum]   [sx/sy/sz] [radius] [z-pos]


```

## materials_phits.inp

```python

$$ ================================================================= $$
$$ ===                material_phits.inp (PHITS)                 === $$
$$ ================================================================= $$

$$ ----------------------------------------------------------------- $$
$$ ---                     Material Section                      --- $$
$$ ----------------------------------------------------------------- $$

[Material]


$$ ----------------------------------------------------------------- $$
$$ ---                     matNum[1] :: Air                      --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: JAERI-Tech-96-001 <-- JAERI-M6928
mat[1]
    H          -1.00000e-03
    C          -1.26000e-02
    N          -7.55000e+01
    O          -2.32000e+01

$ <define> @Air.matNum                =          1
$ <define> @Air.Density               = -0.0012049

$$ ----------------------------------------------------------------- $$
$$ ---                     matNum[2] :: H2O                      --- $$
$$ ----------------------------------------------------------------- $$

mat[2]
    H           2.00000e+00
    O           1.00000e+00

$ <define> @H2O.matNum                =          2
$ <define> @H2O.Density               =       -1.0

$$ ----------------------------------------------------------------- $$
$$ ---                    matNum[3] :: RaCl2                     --- $$
$$ ----------------------------------------------------------------- $$

mat[3]
    226Ra       1.00000e+00
    Cl          2.00000e+00

$ <define> @RaCl2.matNum              =          3
$ <define> @RaCl2.Density             =       -4.9

$$ ----------------------------------------------------------------- $$
$$ ---                      matNum[4] :: Au                      --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: pure gold (Au-197 100%)
mat[4]
    Au          1.00000e+00

$ <define> @Au.matNum                 =          4
$ <define> @Au.Density                =     -19.32

$$ ----------------------------------------------------------------- $$
$$ ---                     matNum[5] :: SiO2                     --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: Quartz-Glass
mat[5]
    Si          1.00000e+00
    O           2.00000e+00

$ <define> @SiO2.matNum               =          5
$ <define> @SiO2.Density              =     -2.196

$$ ----------------------------------------------------------------- $$
$$ ---                      matNum[6] :: Ti                      --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: pure Titanium
mat[6]
    Ti          1.00000e+00

$ <define> @Ti.matNum                 =          6
$ <define> @Ti.Density                =      -4.51

$$ ----------------------------------------------------------------- $$
$$ ---                      matNum[7] :: He                      --- $$
$$ ----------------------------------------------------------------- $$

mat[7]
    He          1.00000e+00

$ <define> @He.matNum                 =          7
$ <define> @He.Density                =  -0.000179

$$ ----------------------------------------------------------------- $$
$$ ---                      matNum[8] :: Ta                      --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: pure Tantal
mat[8]
    Ta          1.00000e+00

$ <define> @Ta.matNum                 =          8
$ <define> @Ta.Density                =    -16.654

$$ ----------------------------------------------------------------- $$
$$ ---                      matNum[9] :: W                       --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: pure Tungsten
mat[9]
    W           1.00000e+00

$ <define> @W.matNum                  =          9
$ <define> @W.Density                 =      -19.3

$$ ----------------------------------------------------------------- $$
$$ ---                     matNum[10] :: Pt                      --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: pure Platinum
mat[10]
    Pt          1.00000e+00

$ <define> @Pt.matNum                 =         10
$ <define> @Pt.Density                =     -21.45

$$ ----------------------------------------------------------------- $$
$$ ---                     matNum[11] :: Al                      --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: pure Aluminum
mat[11]
    Al          1.00000e+00

$ <define> @Al.matNum                 =         11
$ <define> @Al.Density                =       -2.7

$$ ----------------------------------------------------------------- $$
$$ ---                    matNum[12] :: C276                     --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: Hastelloy (Ni-Alloy C-276)
mat[12]
    Ni          5.73000e+01
    Cr          1.55000e+01
    Fe          5.50000e+00
    C           1.00000e-02
    Mn          5.00000e-01
    Si          3.00000e-02
    Mo          1.60000e+01
    W           3.75000e+00
    Co          1.25000e+00
    V           1.50000e-01
    P           5.00000e-03
    S           5.00000e-03

$ <define> @C276.matNum               =         12
$ <define> @C276.Density              =      -8.89

$$ ----------------------------------------------------------------- $$
$$ ---                   matNum[13] :: SUS316                    --- $$
$$ ----------------------------------------------------------------- $$

$$ comment :: Stainless Steel
mat[13]
    Fe         -6.69000e-01
    C          -4.00000e-04
    Si         -1.50000e-04
    Mn         -1.00000e-02
    P          -2.25000e-04
    Ni         -1.20000e-01
    Cr         -1.70000e-01
    Mo         -2.50000e-02

$ <define> @SUS316.matNum             =         13
$ <define> @SUS316.Density            =      -7.98


$$ ----------------------------------------------------------------- $$
$$ ---               matNameColor section (PHITS)                --- $$
$$ ----------------------------------------------------------------- $$

[MatNameColor]
    mat  name               size       color               
    1    Air                2.0        cyan                
    2    H2O                2.0        cyanblue            
    3    RaCl2              2.0        violet              
    4    Au                 2.0        violet              
    5    SiO2               2.0        blue                
    6    Ti                 2.0        darkred             
    7    He                 2.0        pastelcyan          
    8    Ta                 2.0        purple              
    9    W                  2.0        purple              
    10   Pt                 2.0        purple              
    11   Al                 2.0        pink                
    12   C276               2.0        red                 
    13   SUS316             2.0        red                 

```

## tally_fluence_phits.inp

```python
$$
$$ ---------------------------------------------------------- $$
$$ --- [1] tally for fluence calculation                   ---$$
$$ ---------------------------------------------------------- $$
$$
$$

[T-Track]
   mesh =  reg          $$ mesh    :: [ xyz, r-z, reg, tet ]
    reg =  345          $$ region number ::
    volume
     reg     vol
     345     1.0        $$ vol=1.0 => count mode.
 e-type =    2
     ne =  100
   emin =  0.0
   emax =  50.0
   part =  photon
   unit =    2           $$ unit is [1/cm^2/MeV/source]
   axis =  eng
   file =  out/fluence_energy.dat
  x-txt =  energy [MeV]
  y-txt =  track length [photons m/MeV/s]
 epsout =    1


[T-Track]
   mesh =  reg          $$ mesh    :: [ xyz, r-z, reg, tet ]
    reg =  345          $$ region number ::
    volume
     reg     vol
     345     1.0        $$ vol=1.0 => count mode.
 e-type =     5
   edel =  2.302585093    $$ ln(10)  for ln ( Mi+1/Mi )
   emin =  1.0e-10
   emax =  1.0e2
   part =  neutron
   unit =    2           $$ unit is [1/cm^2/MeV/source]
   axis =  eng
   file =  out/fluence_n_energy.dat
  x-txt =  energy [MeV]
  y-txt =  track length [neutrons m/MeV/s]
 epsout =    1


$$
$$ ---------------------------------------------------------- $$
$$ --- [2] tally for fluence 2d                            ---$$
$$ ---------------------------------------------------------- $$
$$
$$

[T-Track]
   mesh =  xyz          $$ mesh    :: [ xyz, r-z, reg, tet ]
 x-type =    2          $$ x-type  :: [ 1: (nx,data[nx+1]), 2:(nx,xmin,xmax), 3:logarithmic ]
     nx =    80
   xmin =  -2.0
   xmax =  +2.0
 y-type =    2
     ny =    1
   ymin =  -2.0
   ymax =  +2.0
 z-type =    2
     nz =   120
   zmin =  -2.0
   zmax =  +4.0
 e-type =    2
     ne =    1
   emin =  0.0
   emax =  1.0e2
   axis =   xz
   part =  photon
   file =  out/fluence_n_xz.dat
  title =  neutrons fluence in xz plane
  gshow =    1
 epsout =    1


[T-Track]
   mesh =  xyz          $$ mesh    :: [ xyz, r-z, reg, tet ]
 x-type =    2          $$ x-type  :: [ 1: (nx,data[nx+1]), 2:(nx,xmin,xmax), 3:logarithmic ]
     nx =    80
   xmin =  -2.0
   xmax =  +2.0
 y-type =    2
     ny =    1
   ymin =  -2.0
   ymax =  +2.0
 z-type =    2
     nz =   120
   zmin =  -2.0
   zmax =  +4.0
 e-type =    2
     ne =    1
   emin =  0.0
   emax =  1.0e2
   axis =   xz
   part =  neutron
   file =  out/fluence_n_xz.dat
  title =  neutrons fluence in xz plane
  gshow =    1
 epsout =    1

```

## tally__cross_phits.inp
```python

$$ ---------------------------------------------------------- $$
$$ --- T-cross   energy specification                     --- $$
$$ ---------------------------------------------------------- $$
$$

[T-Cross]
   mesh =  reg          $$ mesh    :: [ xyz, r-z, reg ]
   reg  =  1            $$ number of surfaces 
   r-from    r-to    area
   371       372     1.0
 e-type =     5
   edel =  2.302585093    $$ ln(10)  for ln ( Mi+1/Mi )
   emin =  1.0e-10
   emax =  1.0e2
 a-type =    -2
     na =     9
   amin =     0
   amax =  90.0
   axis =   eng
   unit =     5    $$ unit :: 4: 1/cm2/sr/MeV/source $$ => count/MeV/s
 output =  a-curr
 factor =  1.0
   part =  neutron
   file =  out/cross_forSource.dat



[T-Cross]
   mesh =  reg          $$ mesh    :: [ xyz, r-z, reg ]
   reg  =  1            $$ number of surfaces 
   r-from    r-to    area
   372       373     1.0
 e-type =     5
   edel =  2.302585093    $$ ln(10)  for ln ( Mi+1/Mi )
   emin =  1.0e-10
   emax =  1.0e2
 a-type =    -2
     na =     9
   amin =     0
   amax =  90.0
   axis =   eng
   unit =     5    $$ unit :: 4: 1/cm2/sr/MeV/source $$ => count/MeV/s
 output =  a-curr
 factor =  1.0
   part =  neutron
   file =  out/cross_forConfirm.dat


```

# 再構成中性子ソースによるpreliminaryの実行結果

- ソース面積変更後再計算まだ、なので、差し替え必要


![[fluence_n.png]]


- 左：フルエンス
- 右：エネルギーあたりの中性子総経路長


# 次の課題

1. 製造量計算コードの整備
2. 固体ターゲットの製造量計算
3. 液体ターゲットの製造量計算
4. 結論のまとめ
Altitude data for test
======================

The area is a tile around Interlaken (BE)

![Extent of tile 1208-4.bt](https://github.com/geoadmin/service-alti/raw/test_data/data/interlaken.png)


    gdalinfo data/swissalti3d/2m/1208-4.bt 
    Driver: BT/VTP .bt (Binary Terrain) 1.3 Format
    Files: data/swissalti3d/2m/1208-4.bt
    Size is 4375, 3000
    Coordinate System is:
    LOCAL_CS["Unknown",
        UNIT["Meter",1]]
    Origin = (628750.000000000000000,176000.000000000000000)
    Pixel Size = (2.000000000000000,-2.000000000000000)
    Corner Coordinates:
    Upper Left  (  628750.000,  176000.000) 
    Lower Left  (  628750.000,  170000.000) 
    Upper Right (  637500.000,  176000.000) 
    Lower Right (  637500.000,  170000.000) 
    Center      (  633125.000,  173000.000) 
    Band 1 Block=1x3000 Type=Float32, ColorInterp=Undefined
      NoData Value=-32768
      Unit Type: m

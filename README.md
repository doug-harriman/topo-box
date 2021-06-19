# topo-box
Small boxes with lids that are topographic reliefs.

![Ouray Colorado](images/usa-colorado-ouray/ouray-1-small.jpg)

# How-To Links
* [Great overview](https://theshamblog.com/making-a-laser-cut-topo-map-the-design-phase/) of creating laser cut topographic map from wood layers from Scott Shambaugh.
* [QGIS to SVG overview](https://dominoc925.blogspot.com/2014/05/qgis-export-layers-to-svg-for.html) on the Dominoc925 blog.
* [3D printing of digital elevation models with QGIS](https://edutechwiki.unige.ch/en/3D_printing_of_digital_elevation_models_with_QGIS) on the EduTech Wiki.
* [3D Printing Terrain Models](https://edutechwiki.unige.ch/en/3D_printing_of_digital_elevation_models_with_QGIS) with QGIS on the EduTech Wiki.
* [Image2STL](https://imagetostl.com/) online converter from grayscale to STL files.

# Tools
* [QGIS](https://www.qgis.org/en/site/) - Free and Open Source Geographic Information System 
  * [DEMto3D](https://plugins.qgis.org/plugins/DEMto3D/) plugin for QGIS.
  * [SimpleSVG](https://plugins.qgis.org/plugins/simplesvg/) plugin for QGIS.
* [TouchTerrain](https://touchterrain.geol.iastate.edu/)
* [HeightMapper](https://tangrams.github.io/heightmapper) Grayscale Image
  * Topo conversion process notes
    * [Load image into Python](https://matplotlib.org/stable/tutorials/introductory/images.html)
    * Since it's grayscale, RGB color channels are the same.  Convert to a Z height matrix by extracting red channel: z = image[:,:,0]  
    * Create a contour plot: ctr = plt.contour(z)
      * Note, we'll need to size appropriately to match the STL unless we do STL here too.  Seems harder
      * Want to map Z values zero to one to the height min/max returned from HeightMapper.  Pint for units conversion.
      * Can then set contour levels desired.  Might add an '+' to the very top.
      * Still need to convert the contour object to an SVG output.
* [Contour Generator](https://contours.axismaps.com/#12/44.3808/-121.7245)

# Colorado, Ouray
* First topo box project.  Did not save model files.
* Milled from 3/4" black walnut ordered on Amazon.
* Model from: https://jthatch.com/Terrain2STL/, did not save exact model, loaded into Fusion360 for milling.
* Surface:
  * Roughed with 2mm ball endmill
  * Finished with 1mm ball endmill, 0.1 mm stepover
* Lettering
  * Clear Expoxy Casting Resin
    * [Purchase](https://www.amazon.com/gp/product/B089XZJFG5)
  * Colorant:  Satin White Synthetic Mica Powder
    * [Purchase](https://www.amazon.com/gp/product/B07KS7WTR2)
    * Tried to mix in manually, did not mix in well enough.  Coloring is inconsistent.  Highly recommend mixing in with a rotary tool.
    * Did not have issues with bubbles and did not degass.  


# Oregon, Black Butte
* [TouchTerrain](https://touchterrain.geol.iastate.edu/?trlat=44.429197180580594&trlon=-121.59384723130317&bllat=44.3616143717882&bllon=-121.68289944838435&DEM_name=USGS/NED&tilewidth=100&printres=0.2&ntilesx=1&ntilesy=1&DEMresolution=14.19&basethick=1&zscale=-25.4&fileformat=STLb&maptype=roadmap&gamma=1&transp=20&hsazi=315&hselev=45&map_lat=44.38402186929164&map_lon=-121.65242965263509&map_zoom=13) model.
* [Oregon GIS](https://spatialdata.oregonexplorer.info/geoportal/search)
* [Oregon Transportation Network](ftp://ftp.gis.oregon.gov/transportation/or_trans_network_public_2019.zip)
* [Grayscale Image](https://tangrams.github.io/heightmapper/#13.19792/44.3946/-121.6303)

# SVG to Fusion360 Surface Mapping
This page discusses how to map and SVG drawing onto a non-planar surface in Fusion360.  
The intent of this action is to create G-Code for Laser etching maps onto topographic reliefs.
In order to laser etch a non-planar surface, we need a G-Code path in 3D so that the laser will remain in focus.

## Mapping Drawings to a Surface
Note: Before starting the process, it is recommended that you further simplify the mesh surface.

1. Create an SVG file.
2. Create a workplane sketch in Fusion360 that is over the surface onto which we will project geometry.
3. Import the SVG file into the sketch. You must be in Design Mode to do this.
4. Edit the sketch.
5. Select: Create -> Project/Include -> Project to Surface
6. Select the 2D sketch geometry and the surface(s) onto which to project them.  With an imported mesh body, there will be many surfaces to select.


## Converting a Line Drawing to a Laser Tool Path
1. Activate Manufacturing Mode
2. Create your setup.
3. Select the "2D Trace" operation.
4. Select the curves projected from above.

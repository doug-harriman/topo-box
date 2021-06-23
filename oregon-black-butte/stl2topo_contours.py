#%%
import matplotlib.pyplot as plt
import numpy as np
from pint import Quantity as Q
from stl import mesh  # https://github.com/WoLpH/numpy-stl/

# TODO: XY size should take a max X and a max Y, then figure out how to fit it.
# TODO: Collect all input variables at the top.
# TODO: Support YAML or basic text config file input.

#%% Scaling
# X/Y scaling comes directly from TouchTerrain.
thickness_base = 1 # Setting from TouchTerrain

model_size_z  =  25  # Z will be scaled to this value.
model_size_xy =  75  # Scale max XY dimension to this value.

#%% Load STL object
# https://touchterrain.geol.iastate.edu/

fn = 'NED_-121.64_44.40_tile_1_1.STL'
m  = mesh.Mesh.from_file(fn)

# Force model corner to origin
m.x -= m.x.min()
m.y -= m.y.min()

# Apply X&Y scalings
if model_size_xy is not None:
    sz_x = m.x.max()
    sz_y = m.y.max()
    if sz_x > sz_y:
        ratio = model_size_xy / sz_x
    else:
        ratio = model_size_xy / sz_y

m.x *= ratio
m.y *= ratio

# Apply Z-scaling
m.z -= thickness_base
scale_z = model_size_z / m.max_[2]  
m.z *= scale_z
m.update_max()
m.update_min()

# Save out updated STL with desired z-scling
m.save(f'scaled-{m.x.max():0.0f}mm-{m.y.max():0.0f}mm-{m.z.max():0.0f}mm.stl')

# Put Z back
m.z /= scale_z

#%% Determine map distances so we can figure out Z scaling.
# Values from TouchTerrain
trlat = np.float64(44.43009951161787)
trlon = np.float64(-121.59661098226607)

bllat = np.float64(44.36171176019724)
bllon = np.float64(-121.68013569742145)

# Haversine Formula
# https://www.movable-type.co.uk/scripts/latlong.html
R            = 6371e3  # [m], Earth's radius in meters

# X calc
phi1         = np.deg2rad(trlat)
phi2         = np.deg2rad(trlat)
delta_phi    = phi1-phi2
delta_lambda = np.deg2rad(bllon-trlon)

a = np.sin(delta_phi/2) * np.sin(delta_phi/2) + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2) * np.sin(delta_lambda/2)
c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
x_dist = R * c # [m]

# Y calc
phi1         = np.deg2rad(trlat)
phi2         = np.deg2rad(bllat)
delta_phi    = phi1-phi2
delta_lambda = np.deg2rad(0)

a = np.sin(delta_phi/2) * np.sin(delta_phi/2) + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2) * np.sin(delta_lambda/2)
c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
y_dist = R * c # [m]

# print(f'x: {x_dist} m')
# print(f'y: {y_dist} m')
# print(f'ratio: {x_dist/y_dist}')

# Determine scaling in each direction
x_scale = x_dist / m.x.max()
y_scale = y_dist / m.y.max()
# print(f'X Scale: {x_scale}')
# print(f'Y Scale: {y_scale}')
xy_scale = np.mean([x_scale,y_scale]) # [m/mm]
xy_scale = Q(xy_scale,'m').to('ft').magnitude # [ft/mm]

# %%
# Create Z values
el_high = Q(1960,'m').to('ft').magnitude        # You have to know the peak of model
el_low  = el_high - m.z.max()*xy_scale*ratio 

# Scale per Geograpic data
el_range = el_high - el_low
print('Elevations')
print(f'  Low  : {el_low:0.0f}')
print(f'  High : {el_high:0.0f}')
print(f'  Range: {el_range:0.0f}')

# TODO: Account for STL base thickness
# * Shift down by base thickness.  Topo 0 elevation should be at 0 now.
# * Apply scaling.  Base thickness will be scaled, but will be negative.
#   
m.z *= el_range / m.z.max()  # Scale for correct elevations.
m.z += el_low                # Offset for base elevation.

#%% STL to height map
# Note: Not getting anything out of the GeoTIFF (expecting a TIFF image)
#       Essentially reversing the mapping to go from a trimesh to a Z matrix of heights.
p = (m.points*1000).astype(np.int32)  # Convert to ints to avoid float eps issues.
r,c = p.shape
p = p.reshape(int(r*c/3),3) 
_,idx = np.unique(p[:,0:2],axis=0,return_index=True)       # Eliminate duplicate trimesh corners, ~12x reduction.
p = p[idx,]
p = p[np.lexsort((p[:,1],p[:,0]))]  # Sort by x, then y.

xv = np.unique(p[:,0])
yv = np.unique(p[:,1])

# Convert Z values to matrix
z = p[:,2]
z = z.reshape(len(xv),len(yv))

# Create x & y matrices
x,y = np.meshgrid(xv,yv)

# Convert everything back to floating point in original units.
x = x.astype(float)/1000
y = y.astype(float)/1000
z = z.astype(float)/1000

#%% Contour Levels
delta_min = 100
delta = 500
level_low  = delta * round(el_low  / delta)
level_high = delta * round(el_high / delta)
levels = np.arange(level_low,level_high,delta)

levels = np.append(levels, delta_min * round(el_low / delta_min) )
levels = np.append(levels, np.floor(el_high))
levels = np.sort(levels)
levels

#%% Create Contours
# x = np.linspace(0,size_x,num=z.shape[0],endpoint=False)
# y = np.linspace(0,size_y,num=z.shape[1],endpoint=False)


ctr = plt.contour(x,y,z.transpose(),levels=levels)
ax = plt.gca()
ax.axis='equal'
cl = ax.clabel(ctr, ctr.levels,  fontsize=4, fmt='%d',inline=True)

#%% Text box size
renderer = plt.figure().canvas.get_renderer()
inv      = ax.transData.inverted()

#%% 
# TODO: Text conversion.  Not that contours do have gaps for text.
# See: https://stackoverflow.com/questions/5320205/matplotlib-text-dimensions
# * ctr has label data stored once labels are generated: ctr.labelTexts[]
# * ctr.labelTexts[i].get_rotation() has rotation of text.  Will need a G-code rotator.
# ** .get_text()
# ** .get_position(): returns x,y tuple
# * Text needs to be rotated in 3D to be normal to surface so that it doesn't go in and out of focus
# ** Need to determine the center coordinate of the text from the text info somehow, in image coordinates
# ** Find the triange from the STL that contains that point.
# ** Get the normal vector for the triangle
# ** Set the text plane normal to the triangle normal

# 3D rotation matrix to align one vector to another
# https://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d
# * Text is generated with a Z unit normal.
# * Find the center of the contour label text box in XY.
# * Find the triangle in the mesh which encloses the label center.
# * Determine the text label center Z-height from that triangle info.
# * Get the triangle unit normal.
# * Generate the label text G-code
# * Translate the label gc to the origin.
# * Calculate the rotation matrix.
# * Rotate the G-Code
# * Translate the G-code
# * Write to file.

#%% Generate Contour G-Code
def Contour2Gcode(ctr,size_z:float=1):
    '''
    Converts Matplotlib contour obect to G-Code lines.
    '''

    # Each segment is associated with a contour level
    # Each segment can be an array of 2D arrays, one per contour line at that level
    # Levels per ctr.levels
    # Note: segments may be empty

    gcode = '''(Machine Setup)
G90  (Absolute Position Mode)
G21  (Units = millimeters)

'''

    # Z scale handling
    z_range  = ctr.zmax - ctr.zmin
    z_scale  = size_z / z_range
    z_offset = ctr.zmin 

    laser_power    = 600
    laser_on_speed = 500

    for i_level,level in enumerate(ctr.levels):
        # If no data, skip
        segments = ctr.collections[i_level].get_segments()
        if len(segments) == 0:
            continue

        # Process each line in the segment
        Z = f'Z{(level-z_offset)*z_scale:0.3f}'
        for segment in segments:
            first_point = True
            for point in segment:
                if first_point:
                    # Go to first point
                    gcode += '\n' + f';Segment Level: {level:0.1f}'  + '\n'
                    gcode += f'G0 X{point[0]:0.3f} Y{point[1]:0.3f} {Z} F1000'+ '\n'
                    first_point = False

                    # Laser on
                    gcode += f'M4 S{laser_power} ;Laser on' + '\n'
                    gcode += f'F{laser_on_speed}' + '\n'

                else:
                    gcode += f'G1 X{point[0]:0.3f} Y{point[1]:0.3f}' + '\n'

            # Laser off at end of segment
            gcode += 'M5        ;Laser off' + '\n'

    gcode += 'M2  ; Job Complete'

    return gcode


gcode = Contour2Gcode(ctr,size_z=model_size_z)
fn_ctr = 'topo_contours.nc'
with open(fn_ctr,'w') as fp:
    fp.write(gcode)

#%% Temporary hack to add tools
import sys
sys.path.append('C:\\src\\3018\\gcode-utilities')

#%% Imports
import re
import matplotlib.pyplot as plt
import numpy as np
from pint import Quantity as Q
from stl import mesh  # https://github.com/WoLpH/numpy-stl/
import trimesh
import gcode_utils
import gcode_doc as gcdoc


# TODO: Collect all input variables at the top.
# TODO: Support YAML or basic text config file input.

#%% Configuration values
# Model material limits
board_thickness = 19.1
planing = 0.5 # per side
base_thickness = 2
model_size_z_max =  board_thickness  # Topology will be scaled to this value.  Base will be extra.
model_size_z_max -= base_thickness
model_size_z_max -= planing * 2

model_size_x_max =  85  # Scale max X dimension.
model_size_y_max =  85  # Scale max Y dimension.

elevation_units   = 'ft'  # Elevation contour units.
contour_delta     = 500   # Main elevation steps.
contour_delta_min = 100   # Initial elevation level above base if not on a main elevation step.

fontsize = 4  # Font size for contour labels

#%% Read in data from log file
fn_log = 'logfile.txt'
with open(fn_log,'r') as fp:
    log = fp.read()

# Extract elevations
re_num = '[+-]?[0-9.]+'
match = re.search(f'elev. min/max: (?P<el_low>{re_num}) (?P<el_high>{re_num})', log)
# elev. min/max: 918.4536743164062 1962.7933349609375 

el_low  = float(match.group('el_low'))
el_high = float(match.group('el_high'))

el_low  = Q(el_low,'m').to(elevation_units).magnitude
el_high = Q(el_high,'m').to(elevation_units).magnitude

# Scaling and base thickness
match = re.search(f'basethick = (?P<thickness_base>{re_num})', log)
thickness_base = float(match.group('thickness_base'))

#%% Load STL objects# https://touchterrain.geol.iastate.edu/
# Black Butte link:
# https://touchterrain.geol.iastate.edu/?trlat=44.43009951161787&trlon=-121.59661098226607&bllat=44.36171176019724&bllon=-121.68013569742145&DEM_name=USGS/NED&tilewidth=100&printres=0.199&ntilesx=1&ntilesy=1&DEMresolution=13.24&basethick=1&zscale=1.0&fileformat=GeoTiff&maptype=roadmap&gamma=1&transp=20&hsazi=315&hselev=45&map_lat=44.40267120931056&map_lon=-121.63846332184082&map_zoom=13
fn_stl = 'NED_-121.64_44.40_tile_1_1.STL'
m  = mesh.Mesh.from_file(fn_stl)

# Force model corner to origin
m.x -= m.x.min()
m.y -= m.y.min()

# Apply X&Y scalings so that model fits in the most constrained dimension
sz_x = m.x.max()
sz_y = m.y.max()
if sz_x > model_size_x_max:
    ratio_x = model_size_x_max / sz_x
if sz_y > model_size_y_max:
    ratio_y = model_size_y_max / sz_y
ratio = np.min([ratio_x,ratio_y])

m.x *= ratio
m.y *= ratio

# Apply Z-scaling
m.z -= thickness_base
scale_z = model_size_z_max / m.max_[2]  
m.z *= scale_z
m.update_max()
m.update_min()

# Save out updated STL with desired z-scling
fn_stl_model = f'scaled-{m.x.max():0.0f}mm-{m.y.max():0.0f}mm-{m.z.max():0.0f}mm.stl'
m.save(fn_stl_model)

# Put Z back
m.z /= scale_z

# %% Z-Scaling for elevation contours
# Geograpic data
el_range = el_high - el_low
print('Elevations')
print(f'  Low  : {el_low:0.0f}')
print(f'  High : {el_high:0.0f}')
print(f'  Range: {el_range:0.0f}')

m.z *= el_range / m.z.max()  # Scale for correct elevations.
m.z += el_low                # Offset for base elevation.

#%% STL to height map
# Note: Not getting anything out of the GeoTIFF (expecting a TIFF image)
#       Essentially reversing the mapping to go from a trimesh to a Z matrix of heights.
p = (m.points*1000).astype(np.int32)  # Convert to ints to avoid float eps issues.
r,c = p.shape
p = p.reshape(int(r*c/3),3) 
_,idx = np.unique(p[:,0:2],axis=0,return_index=True) # Eliminate duplicate trimesh corners, ~12x reduction.
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
level_low  = contour_delta * round(el_low  / contour_delta)
level_high = contour_delta * round(el_high / contour_delta)
levels = np.arange(level_low,level_high,contour_delta)

levels = np.append(levels, contour_delta_min * round(el_low / contour_delta_min) )
levels = np.append(levels, np.floor(el_high))
levels = np.unique(levels)
levels

#%% Create Contours
ctr = plt.contour(x,y,z.transpose(),levels=levels)
ax = plt.gca()
ax.axis='equal'
cl = ax.clabel(ctr, ctr.levels,  fontsize=fontsize, fmt='%d',inline=True)


#%% Query text locations and size
# TODO: Create a heuristic for font size based on model size.  Set the plot size?
# TODO: If plot figure size is set to model XY size, and axis fills figure, then can get direct scaling.
# See: https://stackoverflow.com/questions/5320205/matplotlib-text-dimensions
renderer = plt.figure().canvas.get_renderer()
inv      = ax.transData.inverted()

# Extract text info
lbl_cnt = len(ctr.labelTextsList)
lbl_txt = [x.get_text() for x in ctr.labelTextsList]
lbl_rot = [x.get_rotation() for x in ctr.labelTextsList]
lbl_ctr = [(x._x,x._y,0) for x in ctr.labelTextsList]
lbl_ctr = np.array(lbl_ctr)

# Get the text bounding box.  Note that if the text is rotated, the BB 
# fits the diagonal text.  BB extents do not provide info on text height.
# Rotate the label back to horizontal, then read the new bounding box values.
# From that, extract the text height.
label = ctr.labelTextsList[0]
label.set_rotation(0)
bb = label.get_window_extent(renderer=renderer)
bb = inv.transform(bb)
txt_height = np.diff(bb[:,1])[0]
print(f'Text height: {txt_height:0.1f}mm')

#%% Map text box centers to Z-heights
# At this point we're done with the version of the STL that was scaled
# for real elevations.  We'll load the version of the STL we just created with 
# another package that supports ray tracing so that we can find text locations.
mesh = trimesh.load(fn_stl_model)

# Size the ray direction matrix for number of text labels
ray_z = np.array([[0,0,1]])

# Z-mapping is a slow operation with large STL files. 
# Do point-by-point so we can provide status updates
print(f'Calculating {lbl_cnt} contour elevation labels Z-heights (slow operation)')
idx_tri = np.zeros(lbl_cnt,dtype=int)
for idx, center in enumerate(lbl_ctr):
    print(f'  Mapping label {idx+1} of {lbl_cnt}...',end='',flush=True)
    origin = np.array([[float(center[0]),float(center[1]),0]])

    locations, _, idx_tri[idx] = mesh.ray.intersects_location(ray_origins=origin,
                                                               ray_directions=ray_z)
    lbl_ctr[idx] = locations                                                            
    print('done',flush=True)                                                               

#%% Rotate text labels to map to surface normal
# * Text needs to be rotated in 3D to be normal to surface so that it doesn't go in and out of focus
lbl_norm = mesh.face_normals[idx_tri]

#%% Rotation matrix to go from one vector to another
def RotationV1V2(a:np.array,b:np.array):
    """
    Computes rotation matrix to go from one 3D vector to another.
    Per: https://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d
    """

    # Checks
    if not isinstance(a,np.ndarray):
        raise TypeError("vector a must be a 3D array.")

    if not isinstance(b,np.ndarray):
        raise TypeError("vector b must be a 3D array.")

    if (len(a) != 3) or (len(b) != 3):
        raise TypeError("a and b must be of length 3.")

    # Force unit vectors
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)

    v = np.cross(a, b) 
    s = np.linalg.norm(v) 
    c = np.dot(a, b) 
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]) 
    r = np.eye(3) + vx + np.dot(vx,vx) * (1-c)/(s**2)

    return r


#%%
# Create text label G-Code (created in XY plane)
gcu = gcode_utils.GcodeUtils()
label_gcode = ''
for idx,label in enumerate(lbl_txt):
    # Rotate text 180 degrees if Y normal component is "north"
    rot = lbl_rot[idx]
    if lbl_norm[idx][1] > 0:
        rot += 180

    # Generate label text GCode via gcode_doc
    doc  = gcdoc.Doc(job_control=False)  # Container object for generating G-Code
    gtxt = gcdoc.Text(text=label,size_mm=txt_height,rotation_deg=rot)
    doc.layout.AddChild(gtxt)
    doc.GCode()

    # Position G-Code text via G-Code Utilities
    gcu.gcode = doc.code
    gcu.TranslateCenter()

    # Rotate text to be normal to surface at center of text box.
    R = RotationV1V2(ray_z[0],lbl_norm[idx])
    gcu.Rotate(R)

    # Translate
    gcu.Translate(xyz=lbl_ctr[idx])
    label_gcode += f'\n; Contour Label: {label}\n'
    label_gcode += gcu.gcode

# ** Set the text plane normal to the triangle normal

# 3D rotation matrix to align one vector to another
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

    gcode += label_gcode

    gcode += 'M2  ; Job Complete'

    return gcode

gcode = Contour2Gcode(ctr,size_z=model_size_z_max)
fn_ctr = 'topo_contours.nc'
with open(fn_ctr,'w') as fp:
    fp.write(gcode)

# %%

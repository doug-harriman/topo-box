#svg2topo.py
# Maps SVG path objects onto an STL surface.

# User is responsible for orientation and offsets.

#%% Config
fn_svg = 'artwork/black-butte-roads-simplified.svg'
fn_stl = 'mfg/proto-1/scaled-75mm-85mm-16mm.stl'
fn_gcode = 'roads.nc'


#%% Temporary hack to add tools
import sys
sys.path.append('C:\\src\\3018\\gcode-utilities')

#%% Imports
import re
import numpy as np
import trimesh
import svg_to_gcode as stg   # pip install svg-to-gcode, https://github.com/PadLex/SvgToGcode
import gcode_utils

#%% 
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# Loosen tolerances to reduce point count.  
stg.TOLERANCES['approximation'] = 1

# Instantiate a compiler, specifying the interface type and the speed at which the tool should move. pass_depth controls
# how far down the tool moves after every pass. Set it to 0 if your machine does not support Z axis movement.
gcode_compiler = stg.compiler.Compiler(stg.compiler.interfaces.Gcode, 
                                       movement_speed=1000, 
                                       cutting_speed=300, 
                                       custom_header=['G90','G21','M5'],
                                       pass_depth=0)

curves = stg.svg_parser.parse_file(fn_svg) # Parse an svg filefn_svg into geometric curves

gcode_compiler.append_curves(curves) 
gcode_compiler.compile_to_file(fn_gcode) #, passes=1)

# When the laser is off, it's a G0 move.  G1->G0
# This is not strictly necessary, but helps with visualization via ncviewer.com.
gcu = gcode_utils.GcodeUtils()
gcu.Load(fn_gcode)

def G1_to_G0(m):
    s = m.group(0)
    s = s.replace('G1','G0')
    return s

gcu.gcode = re.sub('M5;\s*.*\s*M3',G1_to_G0,gcu.gcode)

# Pixels are at 96 DPI, and we want to convert to mm.
scale = 25.4/96
gcu.Scale(scale_factor=scale)

# Push to origin at lower left
gcu.TranslateLowerLeft()

gcu.Save()

#%% Z Height Mapping
# # At this point we're done with the version of the STL that was scaled
# for real elevations.  We'll load the version of the STL we just created with 
# another package that supports ray tracing so that we can find text locations.
mesh = trimesh.load(fn_stl)

# Size the ray direction matrix for number of text labels
ray_z = np.array([[0,0,1]])
pts_cnt = np.array(0)

re_num = '[+-]?[0-9.]+'
re_xy = re.compile(f'X({re_num})\s*Y({re_num})')
def CalcZHeight(m):
    # Get our point
    x = m.group(1)
    y = m.group(2)
    xyz = np.asarray([[x,y,0]],float)

    # Find the Z-height
    xyz = mesh.ray.intersects_location(ray_origins=xyz, ray_directions=ray_z)
    xyz = xyz[0][0]

    # Write the data back
    s = f'X{xyz[0]} Y{xyz[1]} Z{xyz[2]:0.3f}'

    return s

gcu.gcode = re_xy.sub(CalcZHeight,gcu.gcode)#,count=20)
gcu.SaveAs(gcu.filename + '-updated.nc')


#%% 
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

#%%
import matplotlib.pyplot as plt
import matplotlib.image  as img
from matplotlib.tri import Triangulation
# from mpl_toolkits import plt3
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pint import Quantity as Q

#%%
fn = 'heightmapper-1624123293352.png'  # Just surface
# fn = 'heightmapper-1624119991507.png'  # With cyan roads
im = img.imread(fn)
plt.imshow(im)
ax = plt.gca()
ax.axis='equal'


# %%
# Create Z values
z = im[:,:,0]
z = np.flipud(z)

# Scale per Geograpic data
el_low  = Q( 936,'m').to('ft')
el_high = Q(1960,'m').to('ft')
el_range = el_high - el_low
print('Elevations')
print(f'  Low  : {el_low:0.0f}')
print(f'  High : {el_high:0.0f}')
print(f'  Range: {el_range:0.0f}')

z *= el_range.magnitude
z += el_low.magnitude

#%%
# 3D plot
# X&Y based on size of image.
# TODO: Scale this to get mm of size of plot.
# x,y = z.shape
# x, y = np.meshgrid(range(z.shape[0]), range(z.shape[1]))

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.plot_surface(x, y, z)
# plt.title('z as 3d height map')
# plt.show()

# # show hight map in 2d
# plt.figure()
# plt.title('z as 2d heat map')
# p = plt.imshow(z)
# plt.colorbar(p)
# plt.show()


#%% 
# Write the surface to STL
# https://github.com/WoLpH/numpy-stl/issues/19
# Port this: https://www.mathworks.com/matlabcentral/fileexchange/4512-surf2stl

#%%
delta_min = 100
delta = 500
level_low  = delta * round(z.min() / delta)
level_high = delta * round(z.max() / delta)
levels = np.arange(level_low,level_high,delta)

levels = np.append(levels, delta_min * round(z.min() / delta_min) )
levels = np.append(levels, np.floor(z.max()))
levels = np.sort(levels)
levels

#%%

ctr = plt.contour(z,levels=levels)
ax = plt.gca()
ax.axis='equal'
cl = ax.clabel(ctr, ctr.levels,  fontsize=4, fmt='%d',inline=True)

#%% 
# Extracting contour lines
# seg = ctr.collections[1].get_segments()

# TODO: Units conversion. Contour x,y in pixels, z in feet at this point.
#       * Update contour generation to use scaled x,y so that portion is handled.
#       * x & y in CNC units for part fabriction.
#       * pass in Z scaling for mountain elevation to CNC units.
# TODO: Need job setup header, laser on/off control.

# TODO: Text conversion.  Not that contours do have gaps for text.
# * No idea how to deal with font sizes.  May just have to skip
# * ctr has label data stored once labels are generated: ctr.labelTexts[]
# * ctr.labelTexts[i].get_rotation() has rotation of text.  Will need a G-code rotator.
# ** .get_text()
# ** .get_position(): returns x,y tuple

def Contour2Gcode(ctr):
    '''
    Converts Matplotlib contour obect to G-Code lines.
    '''

    # Each segment is associated with a contour level
    # Each segment can be an array of 2D arrays, one per contour line at that level
    # Levels per ctr.levels
    # Note: segments may be empty

    gcode = ''

    for i_level,level in enumerate(ctr.levels):
        # If no data, skip
        segments = ctr.collections[i_level].get_segments()
        if len(segments) == 0:
            continue

        # Process each line in the segment
        Z = f'Z{level:0.3f}'
        for segment in segments:
            first_point = True
            for point in segment:
                if first_point:
                    # Go to first point
                    # TODO: Laser on
                    gcode += '\n' + f';Segment Level: {level:0.1f}'  + '\n'
                    gcode += f'G0 X{point[0]:0.3f} Y{point[1]:0.3f} {Z} F1000'+ '\n'
                    first_point = False
                else:
                    gcode += f'G1 X{point[0]:0.3f} Y{point[1]:0.3f} F500' + '\n'

    return gcode

gcode = Contour2Gcode(ctr)
fn_ctr = 'contours.nc'
with open(fn_ctr,'w') as fp:
    fp.write(gcode)


# %%
# Save file
plt.savefig('topo.svg')
# %%

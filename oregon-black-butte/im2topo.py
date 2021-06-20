#%%
import matplotlib.pyplot as plt
import matplotlib.image  as img
import numpy as np
from pint import Quantity as Q

#%%
fn = 'heightmapper-1624123293352.png'  # Just surface
# fn = 'heightmapper-1624119991507.png'  # With cyan roads
# fn = 'heightmapper-cyan.png'  # Closeup of cyan stuff
im = img.imread(fn)
plt.imshow(im)
ax = plt.gca()
ax.axis='equal'

#%% Scaling
size_xy = 100  # Min xy dimension will be this value.
size_z  =  25  # Z will be scaled to this value.

#%% Finding roads
# Look for colors that are not gray.
gray_idx_x,gray_idx_y = np.where(np.isclose(im[:,:,0],im[:,:,1]) & np.isclose(im[:,:,1],im[:,:,2]))

# Create a roads image
im_roads = np.zeros(im.shape) # Black image
im_roads[gray_idx_x,gray_idx_y,:] = np.ones(4) # Set all the grayscale to white.

# Show just the roads
plt.imshow(im_roads)


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

#%% Part sizes.
x,y = z.shape
if x<y:
    size_x = size_xy
    size_y = size_xy * y/x
else:
    size_y = size_xy
    size_yx= size_xy * x/y

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

#%% Contour Levels
delta_min = 100
delta = 500
level_low  = delta * round(z.min() / delta)
level_high = delta * round(z.max() / delta)
levels = np.arange(level_low,level_high,delta)

levels = np.append(levels, delta_min * round(z.min() / delta_min) )
levels = np.append(levels, np.floor(z.max()))
levels = np.sort(levels)
levels

#%% Create Contours

x = np.linspace(0,size_x,num=z.shape[0],endpoint=False)
y = np.linspace(0,size_y,num=z.shape[1],endpoint=False)


ctr = plt.contour(y,x,z,levels=levels)
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
# * Text needs to be rotated in 3D to be normal to surface so that it doesn't go in and out of focus
# ** Need to determine the center coordinate of the text from the text info somehow, in image coordinates
# ** Find the triange from the STL that contains that point.
# ** Get the normal vector for the triangle
# ** Set the text plane normal to the triangle normal
def Contour2Gcode(ctr,size_z:float=1):
    '''
    Converts Matplotlib contour obect to G-Code lines.
    '''

    # Each segment is associated with a contour level
    # Each segment can be an array of 2D arrays, one per contour line at that level
    # Levels per ctr.levels
    # Note: segments may be empty

    gcode = ''

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

    return gcode


gcode = Contour2Gcode(ctr,size_z=size_z)
fn_ctr = 'contours.nc'
with open(fn_ctr,'w') as fp:
    fp.write(gcode)



# %%

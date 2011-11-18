import os
import platform
from openalea.core.path import path
from openalea.plantgl.all import *

windows = platform.system() is 'Windows'

def povray2(pov_file, height=320, width=280, image_name=''):
    '''    
    '''
    image = None; 
    # write the node code here.

    f = path(pov_file)
    namebase = f.namebase
    ext = f.ext
    dirname = f.dirname()

    old_dir = os.path.abspath(os.getcwd())
    os.chdir(dirname)

    if not image_name:
        image_name = dirname / namebase +'.png'

    image_name = path(image_name)
    if image_name.exists():
        image_name.remove()

    cmdline = 'povray +I%s +H%d +W%d'%(pov_file, height, width)
    os.system(cmdline)
    # return outputs
    os.chdir(old_dir)

    return image_name,

def povray(scene, 
           pov_file = './scene.pov', 
           camera_distance=1., fov=45., width=320, height=280, 
           domain = ((0.,0.),(1.,1.)), 
           azimuth=0., zenith= 0., camera_type = 'perspective', 
           soil=False, 
           povray_cmd='povray'):
    """    
    Compute povray file based on a scene.

    :Parameters:
        - scene: a plantgl scene
        - camera distance: distance from the position of the camera to the look_at point
        - angle : angle corresponding to the width of the image
        - width: width of the final image in pixel
        - height: height of the final image in pixel
        - domain: scene pattern used by caribu
        - azimuth: angle in degree around the vertical axis. az=0. is equialent to have the width of the image align to X direction of the scene
        - zenith: angle between the view direction and the vertical
        - camera type: perspective, orthographic or fisheye
        - soil: add a soil to the scene
        - povray cmd : the path of the povray exe
    """

    # color elements based on the optical properties
    
    t=Tesselator()
    mesh_fn = pov_file[0:-4]+'_mesh.pov'
    pov = PovFilePrinter(mesh_fn, t)
    scene.apply(pov)

    # Write the camera in the main pov file
    #pov_camera = pov_header(...)
    pov_camera = """
camera {{
    {camera}
    location <0,0,{tz:.2f}>
    direction <0,0,-1>
    right <{width:d}/{height:d},0,0>
    look_at <0,0,0 >
    angle {fov:n}

    rotate <{zenith:.2f},0,0>
    rotate <0,0,{azimuth:.2f}>
    translate <{tx:.2f},{ty:.2f},0>
}}

    """

    x=0.5*(domain[0][0]+domain[1][0])
    y=0.5*(domain[0][1]+domain[1][1])
    pov_camera = pov_camera.format(camera=camera_type, tz=camera_distance, fov=fov, azimuth=azimuth, 
                      zenith=zenith, tx=x, ty=y, width=width, height=height)
    
    #print pov_camera

    f = path(pov_file)
    namebase = f.namebase
    ext = f.ext
    dirname = f.dirname()

    povf = f.open(mode='w')
    pov_header(povf, pov_camera, domain=domain, soil=soil)
    povf.write('#include "{mesh_fn}"\n'.format(mesh_fn=mesh_fn))
    povf.close()

    old_dir = os.path.abspath(os.getcwd())
    os.chdir(dirname)

    if windows:
        image_name = dirname / namebase +'.bmp'
    else:
        image_name = dirname / namebase +'.png'

    image_name = path(image_name)
    if image_name.exists():
        image_name.remove()

    if windows:
        cmdline = 'pvengine +I%s +H%d +W%d -d /exit'%(pov_file, height, width)
    else:
        cmdline = '%s +I%s +H%d +W%d'%(povray_cmd, pov_file, height, width)
    os.system(cmdline)
    # return outputs
    os.chdir(old_dir)

    return image_name,

def pov_header(f, pov_camera, background = (0,0,0), light = (10,0,10), domain = ((0.,0.),(1.,1.)), soil=False):
    """ Write the header of  povray file. """
    f.write("/"*80+"\n")
    f.write("#include \"colors.inc\""+"\n\n")
    f.write(pov_camera+"\n")
    x,y,z=light
    f.write("light_source {{  <{tx},{ty},{tz}> color rgb <1,1,1>}}\n\n".format(tx=x,ty=y,tz=z))
    r,g,b = background
    f.write("background {{ color rgb < {cr},{cg},{cb}> }}\n\n".format(cr=r,cg=g,cb=b))
    
    if soil:
        (x1,y1),(x2,y2) = domain
        s = """
#declare T1=
    texture {{
      pigment {{ color red 1.0 green 0.75 blue 0.33 }}
      normal {{bumps 0.4  scale 0.007}} 
}}

#declare T2=
 texture{{
   pigment{{color red 1.0 green 0.75 blue 0.33}}
   normal {{granite 0.6 scale 0.1 }}
   finish {{phong 0.8 phong_size 200}} 
}}

box {{ <{x1}, {y1},  -0.1>,  
    < {x2}, {y2}, 0>   
    texture {{T2}} }}
"""
        text = s.format(x1=x1,y1=y1,x2=x2,y2=y2)
        print text
        f.write(text)
        


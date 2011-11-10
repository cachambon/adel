
# This file has been generated at Tue Feb 12 14:41:01 2008

from openalea.core import *


__name__ = 'alinea.adel.povray'
__alias__ = []

__editable__ = True
__version__ = '0.9.1'
__description__ = 'Use of povray to compute coverage rate'
__license__ = 'CECILL'
__authors__ = 'C. Pradal'
__url__ = ''
__institutes__ = 'CIRAD, INRIA'
 

__all__ = []

color_list=[(0,0,0),
            (255,0,0),
            (0,255,0),
            (0,0,255),
            (255,255,0),
            (0,255,255),
            (255,0,255),
            (128,255,0),
            (0,128,255),
            (255,0,128),
            (0,255,128),
            (128,0,255),
            (255,128,0),
            (128,128,255),
            (255,128,128),
            (128,255,128),
            (255,255,255)
            ]


povray = Factory(name='povray', 
                category='image', 
                nodemodule='povray',
                nodeclass='povray',
                outputs=[{'interface': IFileStr, 'name': 'povray image'}],
                )

__all__.append('povray')

color_item = Factory(name='col_item', 
                category='color', 
                nodemodule='color',
                nodeclass='col_item',
                inputs=[dict(interface='IInt', name='color index', value=None, desc='color index. If None, return a function'),
                        dict(interface='ISequence', name='color list', value=color_list),
                        ],
                outputs=[{'interface': IRGBColor, 'name': 'color list'}],
                )

__all__.append('color_item')


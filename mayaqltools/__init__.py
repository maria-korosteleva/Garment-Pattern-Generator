"""
    Package for to simulate garments from patterns in Maya with Qualoth
    Note that Maya uses Python 2.7 (incl Maya 2020) hence this package is adapted to Python 2.7

    Main dependencies:
        * Maya 2018+
        * Arnold Renderer
        * Qualoth (compatible with your Maya version)
    
    To run the package in Maya don't foget to add it to PYTHONPATH!
"""
import mayascene
reload(mayascene)

from .mayascene import MayaGarment, Scene, MayaGarmentWithUI

import simulation
import qualothwrapper
import garmentUI

reload(simulation)
reload(qualothwrapper)
reload(garmentUI)

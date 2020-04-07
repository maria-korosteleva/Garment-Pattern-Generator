"""
    Module to batch-simulate garments from patterns in Maya.
    Note that Maya uses Python 2.7 (incl Maya 2020) hence this module is adapted to Python 2.7
"""
# Basic
from __future__ import print_function
import json
from os import path
import numpy as np

# Maya
import maya.cmds

# My module
from pattern.core import BasicPattern


class MayaPattern(BasicPattern):
    """
    Extends a pattern specification in custom JSON format to work with Maya
        Input:
            * Pattern template in custom JSON format
        * import panel to Maya scene TODO
        * cleaning imported stuff TODO
        * Basic operations on panels in Maya TODO
    """
    def __init__(self, pattern_file):
        pat = BasicPattern(pattern_file)
        print(issubclass(pat.__class__, object))
        super(BasicPattern, self).__init__(pattern_file)
    
    def load(self):
        print("All panels loaded to Maya")


if __name__ == "__main__":
    pattern = MayaPattern(
        'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_per_panel.json'
    )
    pattern.load()

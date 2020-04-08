"""
    Qualoth scripts are written in MEL. 
    This module makes a python interface to them
    Note that's Python 2.7-friendly
"""
from __future__ import print_function

from maya import mel
from maya import cmds


def load_plugin():
    """
        Forces loading Qualoth plugin into Maya. 
        Note that plugin should be installed and licensed to use it!
        Inquire here: http://www.fxgear.net/vfxpricing
    """
    maya_year = mel.eval('getApplicationVersionAsFloat')
    plugin_name = 'qualoth_' + str(maya_year) + '_x64'
    print('Loading ', plugin_name)
    
    cmds.loadPlugin(plugin_name)


# -------- Wrappers -----------
# Make sure that Qualoth plugin is loaded before running any wrappers!

def qlCreateCollider(cloth, body):
    """
        Marks body as a collider object for cloth --
        eshures that cloth won't penetrate body when simulated
    """
    cmds.select([cloth, body])
    # Operates on selection
    mel.eval('qlCreateCollider()')

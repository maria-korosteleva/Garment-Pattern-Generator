"""
    Maya interface for editing & testing template files
    Python 2.7 compatible
    * Maya 2018+
    * Qualoth
"""
# Basic
from __future__ import print_function
from __future__ import division
from functools import partial
from datetime import datetime
import os
import numpy as np

# Maya
from maya import cmds
import maya.mel as mel

# My modules
import simulation as mysim
import customconfig
reload(mysim)
reload(customconfig)


# ----- State -------
class State(object):
    def __init__(self):
        self.garment = None
        self.scene = None
        self.save_to = None
        self.config = customconfig.Properties()
        mysim.init_sim_props(self.config)  # use default setup for simulation -- for now


# ----- Callbacks -----
def sample_callback(text):
    print('Called ' + text)
    

def template_field_callback(view_field, state):
    """Get the file with pattern"""
    multipleFilters = "JSON (*.json);;All Files (*.*)"
    template_file = cmds.fileDialog2(
        fileFilter=multipleFilters, 
        dialogStyle=2, 
        fileMode=1, 
        caption='Choose pattern specification file'
    )
    if not template_file:  # do nothing
        return
    template_file = template_file[0]

    cmds.textField(view_field, edit=True, text=template_file)

    # create new grament
    state.garment = mysim.mayasetup.MayaGarment(template_file, True)  # previous object will autoclean
    if state.scene is not None:
        reload_garment_callback(state)


def load_body_callback(view_field, state):
    """Get body file & (re)init scene"""
    multipleFilters = "OBJ (*.obj);;All Files (*.*)"
    file = cmds.fileDialog2(
        fileFilter=multipleFilters, 
        dialogStyle=2, 
        fileMode=1, 
        caption='Choose body obj file'
    )
    if not file:  # do nothing
        return 

    file = file[0]
    cmds.textField(view_field, edit=True, text=file)

    state.config['body'] = os.path.basename(file)  # update info
    state.scene = mysim.mayasetup.Scene(file, state.config['render'], clean_on_die=True)  # previous scene will autodelete
    if state.garment is not None:
        reload_garment_callback(state)
            

def reload_garment_callback(state):
    """
        (re)loads current garment object to Maya if it exists
    """
    if state.garment is None or state.scene is None:
        cmds.confirmDialog(title='Error', message='Load pattern specification & body info first')
        return

    state.garment.clean(True)
    state.garment.load()
    state.garment.setMaterialProps(state.scene.cloth_shader)
    state.garment.add_colliders(state.scene.body, state.scene.floor)


def sim_callback(state):
    """ Start simulation """
    if state.garment is None or state.scene is None:
        cmds.confirmDialog(title='Error', message='Load pattern specification & body info first')
        return
    print('Simulating..')
    mysim.qw.qlCleanSimCache()
    mysim.qw.start_maya_sim(state.garment, state.config['sim'])


def clean_scene_callback(state):
    """Remove existing garment from the scene"""
    if state.garment is not None:
        state.garment.clean(True)  # Delete maya objects for smooth operation of future simulations


def win_closed_callback():
    """Clean-up"""
    # Remove solver objects from the scene
    cmds.delete(cmds.ls('qlSolver*'))
    # Other created objects will be automatically deleted through destructors


def saving_folder_callback(view_field, state):
    """Choose folder to save files to"""
    directory = cmds.fileDialog2(
        dialogStyle=2, 
        fileMode=3,  # directories 
        caption='Choose body obj file'
    )
    if not directory:  # do nothing
        return 

    directory = directory[0]
    cmds.textField(view_field, edit=True, text=directory)

    state.save_to = directory


def _new_dir(root_dir, tag='snap'):
    """create fresh directory for saving files"""
    folder = tag + '_' + datetime.now().strftime('%y%m%d-%H-%M-%S')
    path = os.path.join(root_dir, folder)
    os.makedirs(path)
    return path


def quick_save_callback(view_field, state):
    """Quick save with pattern spec and sim config"""
    if state.save_to is None:
        saving_folder_callback(view_field, state)
    
    new_dir = _new_dir(state.save_to, state.garment.name)
    # serialize
    state.garment.serialize(new_dir, to_subfolder=False)
    state.config.serialize(os.path.join(new_dir, 'sim_props.json'))


def full_save_callback(view_field, state):
    """Full save with pattern spec, sim config, garment mesh & rendering"""
    if state.save_to is None:
        saving_folder_callback(view_field, state)
    
    new_dir = _new_dir(state.save_to, state.garment.name)
    # serialize
    state.garment.serialize(new_dir, to_subfolder=False)
    state.config.serialize(os.path.join(new_dir, 'sim_props.json'))
    state.garment.save_mesh(new_dir)
    state.scene.render(new_dir)


# --------- UI Drawing ----------
def equal_rowlayout(num_columns, win_width, offset):
    """Create new layout with given number of columns + extra columns for spacing"""
    total_cols = num_columns * 2 - 1
    col_width = []
    for col in range(1, num_columns + 1):
        col_width.append((col, win_width / num_columns - offset))

    col_attach = [(col, 'both', offset) for col in range(1, num_columns + 1)]

    return cmds.rowLayout(
        numberOfColumns=num_columns,
        columnWidth=col_width, 
        columnAttach=col_attach, 
    )


def init_UI(state):
    """Initialize interface"""
    # init window
    window_width = 400
    main_offset = 10
    win = cmds.window(
        title="Template editing", width=window_width, 
        closeCommand=win_closed_callback
    )
    top_layout = cmds.columnLayout(columnAttach=('both', main_offset), rowSpacing=10, adj=1)

    # ------ Draw GUI -------
    # Setup
    # Pattern load
    cmds.rowLayout(nc=3, adj=2)
    cmds.text(label='Pattern spec: ')
    template_filename_field = cmds.textField(editable=False)
    cmds.button(
        label='Load', backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
        command=lambda *args: template_field_callback(template_filename_field, state))   
    # Body load
    cmds.setParent('..')
    cmds.rowLayout(nc=3, adj=2)
    cmds.text(label='Body file: ')
    body_filename_field = cmds.textField(editable=False)
    cmds.button(
        label='Load', backgroundColor=[227 / 256, 255 / 256, 119 / 256], 
        command=lambda *args: load_body_callback(body_filename_field, state))
    # separate
    cmds.setParent('..')
    cmds.separator()

    # Pattern description 
    state.pattern_layout = cmds.columnLayout(columnAttach=('both', 0), rowSpacing=main_offset)
    filename_field = cmds.text(label='<pattern_here>', al='left')
    
    # separate
    cmds.setParent('..')
    cmds.separator()
    # Operations
    equal_rowlayout(3, win_width=window_width, offset=main_offset)
    cmds.button(label='Reload', backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
                command=lambda *args: reload_garment_callback(state))
    cmds.button(label='Start Sim', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
                command=lambda *args: sim_callback(state))
    cmds.button(label='Clean', backgroundColor=[255 / 256, 140 / 256, 73 / 256], 
                command=lambda *args: clean_scene_callback(state))

    # separate
    cmds.setParent('..')
    cmds.separator()

    # Saving folder
    cmds.rowLayout(nc=3, adj=2)
    cmds.text(label='Saving to: ')
    saving_to_field = cmds.textField(editable=False)
    cmds.button(
        label='Choose', backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
        command=lambda *args: saving_folder_callback(saving_to_field, state))
    # saving requests
    cmds.setParent('..')
    equal_rowlayout(2, win_width=window_width, offset=main_offset)
    cmds.button(label='Save snapshot', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
                command=lambda *args: quick_save_callback(saving_to_field, state), 
                ann='Quick save with pattern spec and sim config')
    cmds.button(label='Save with 3D', backgroundColor=[255 / 256, 140 / 256, 73 / 256], 
                command=lambda *args: full_save_callback(saving_to_field, state), 
                ann='Full save with pattern spec, sim config, garment mesh & rendering')

    # Last
    cmds.setParent('..')
    cmds.text(label='')    # offset

    # fin
    cmds.showWindow(win)


# -------------- Main -------------
def main():
    global_state = State()  
    mysim.qw.load_plugin()

    # Relying on python passing objects by reference
    init_UI(global_state)


if __name__ == "__main__":
    main()

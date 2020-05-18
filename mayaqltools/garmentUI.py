"""
    Maya interface for editing & testing patterns files
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
import mayaqltools as mymaya
import customconfig


# -------- Main call -------------
def start_GUI():
    """Initialize interface"""

    # Init state
    state = State()  

    # init window
    window_width = 400
    main_offset = 10
    win = cmds.window(
        title="Template editing", width=window_width,
        closeCommand=win_closed_callback, 
        topEdge=15
    )
    cmds.columnLayout(columnAttach=('both', main_offset), rowSpacing=10, adj=1)

    # ------ Draw GUI -------
    # Pattern load
    text_button_group(template_field_callback, state, label='Pattern spec: ', button_label='Load')
    # body load
    text_button_group(load_body_callback, state, label='Body file: ', button_label='Load')
    # props load
    text_button_group(load_props_callback, state, label='Properties: ', button_label='Load')
    # scene setup load
    text_button_group(load_scene_callback, state, label='Scene: ', button_label='Load')
    # separate
    cmds.separator()

    # Pattern description 
    state.pattern_layout = cmds.columnLayout(
        columnAttach=('both', 0), rowSpacing=main_offset, adj=1)
    cmds.text(label='<pattern_here>', al='left')
    cmds.setParent('..')
    # separate
    cmds.separator()

    # Operations
    equal_rowlayout(2, win_width=window_width, offset=main_offset)
    cmds.button(label='Reload from JSON', backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
                command=partial(reload_garment_callback, state))
    sim_button = cmds.button(label='Start Sim', backgroundColor=[227 / 256, 255 / 256, 119 / 256])
    cmds.button(sim_button, edit=True, 
                command=partial(start_sim_callback, sim_button, state))
                             
    cmds.setParent('..')
    # separate
    cmds.separator()

    # Saving folder
    saving_to_field = text_button_group(saving_folder_callback, state, 
                                        label='Saving to: ', button_label='Choose')
    # saving requests
    equal_rowlayout(2, win_width=window_width, offset=main_offset)
    cmds.button(label='Save snapshot', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
                command=partial(quick_save_callback, saving_to_field, state), 
                ann='Quick save with pattern spec and sim config')
    cmds.button(label='Save with 3D', backgroundColor=[255 / 256, 140 / 256, 73 / 256], 
                command=partial(full_save_callback, saving_to_field, state), 
                ann='Full save with pattern spec, sim config, garment mesh & rendering')
    cmds.setParent('..')

    # Last
    cmds.text(label='')    # offset

    # fin
    cmds.showWindow(win)


# ----- State -------
class State(object):
    def __init__(self):
        self.pattern_layout = None  # to de set on UI init
        self.garment = None
        self.scene = None
        self.save_to = None
        self.saving_prefix = None
        self.body_file = None
        self.config = customconfig.Properties()
        self.scenes_path = ''
        mymaya.simulation.init_sim_props(self.config)  # use default setup for simulation -- for now

    def reload_garment(self):
        """Reloads garment Geometry & UI with current scene. 
            JSON is NOT loaded from disk as it's on-demand operation"""
        if self.garment is None:
            return 

        if self.scene is not None:
            self.garment.load(
                shader_group=self.scene.cloth_SG(), 
                obstacles=[self.scene.body, self.scene.floor()]
            )
        else:
            self.garment.load()

        # calling UI after loading for correct connection of attributes
        self.garment.drawUI(self.pattern_layout)

    def fetch(self):
        """Update info in deendent object from Maya"""
        self.scene.fetch_props_from_Maya()
        self.config.set_section_config(
            'sim', 
            material=self.garment.fetchMaterialSimProps()
        )
    
    def serialize(self, directory):
        """Serialize text-like objects"""
        self.config.serialize(os.path.join(directory, 'sim_props.json'))
        self.garment.serialize(directory, to_subfolder=False)

    def save_scene(self, directory):
        """Save scene objects"""
        self.garment.save_mesh(directory)
        self.scene.render(directory, self.garment.name)


# ------- Errors --------
class CustomError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return(self.__class__.__name__ + ', {0} '.format(self.message))
        else:
            return(self.__class__.__name__)


class SceneSavingError(CustomError):
    def __init__(self, *args):
        super(SceneSavingError, self).__init__(*args)


# --------- UI Drawing ----------
def equal_rowlayout(num_columns, win_width, offset):
    """Create new layout with given number of columns + extra columns for spacing"""
    col_width = []
    for col in range(1, num_columns + 1):
        col_width.append((col, win_width / num_columns - offset))

    col_attach = [(col, 'both', offset) for col in range(1, num_columns + 1)]

    return cmds.rowLayout(
        numberOfColumns=num_columns,
        columnWidth=col_width, 
        columnAttach=col_attach, 
    )


def text_button_group(callback, state, label='', button_label='Click'):
    """Custom version of textFieldButtonGrp"""
    cmds.rowLayout(nc=3, adj=2)
    cmds.text(label=label)
    text_field = cmds.textField(editable=False)
    cmds.button(
        label=button_label, 
        bgc=[0.99, 0.66, 0.46],  # backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
        command=partial(callback, text_field, state))
    cmds.setParent('..')
    return text_field


# ----- Callbacks -----
def sample_callback(text, *args):
    print('Called ' + text)
    

def template_field_callback(view_field, state, *args):
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
    state.garment = mymaya.MayaGarmentWithUI(template_file, True)  # previous object will autoclean
    state.reload_garment()


def load_body_callback(view_field, state, *args):
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
    state.body_file = file
    state.scene = mymaya.Scene(file, state.config['render'], scenes_path=state.scenes_path, clean_on_die=True)  # previous scene will autodelete
    state.reload_garment()
            

def load_props_callback(view_field, state, *args):
    """Load sim & renderign properties from file rather then use defaults"""
    multipleFilters = "JSON (*.json);;All Files (*.*)"
    file = cmds.fileDialog2(
        fileFilter=multipleFilters, 
        dialogStyle=2, 
        fileMode=1, 
        caption='Choose sim & rendering properties file'
    )
    if not file:  # do nothing
        return

    file = file[0]
    cmds.textField(view_field, edit=True, text=file)
    
    # update props, fill in the gaps
    state.config = customconfig.Properties(file)
    mymaya.simulation.init_sim_props(state.config)  # fill the empty parts

    # Use current body info instead of one from config
    if state.body_file is not None:
        state.config['body'] = os.path.basename(state.body_file)

    # Update scene with new config
    if state.scene is not None:
        state.scene = mymaya.Scene(
            state.body_file, state.config['render'], 
            scenes_path=state.scenes_path, clean_on_die=True)  
        state.reload_garment()
    
    # Load material props
    if state.garment is not None:
        state.garment.setMaterialSimProps(state.config['sim']['config']['material'])


def load_scene_callback(view_field, state, *args):
    """Load sim & renderign properties from file rather then use defaults"""
    multipleFilters = "MayaBinary (*.mb);;All Files (*.*)"
    file = cmds.fileDialog2(
        fileFilter=multipleFilters, 
        dialogStyle=2, 
        fileMode=1, 
        caption='Choose scene setup Maya file'
    )
    if not file:  # do nothing
        return

    file = file[0]
    cmds.textField(view_field, edit=True, text=file)

    # Use current scene info instead of one from config
    state.config['render']['config']['scene'] = os.path.basename(file)
    state.scenes_path = os.path.dirname(file)

    # Update scene with new config
    if state.scene is not None:
        # del state.scene
        state.scene = mymaya.Scene(
            state.body_file, state.config['render'], 
            scenes_path=state.scenes_path,
            clean_on_die=True)  
        state.reload_garment()


def reload_garment_callback(state, *args):
    """
        (re)loads current garment object to Maya if it exists
    """
    if state.garment is not None:
        state.garment.reloadJSON()
        state.reload_garment()
    

def start_sim_callback(button, state, *args):
    """ Start simulation """
    if state.garment is None or state.scene is None:
        cmds.confirmDialog(title='Error', message='Load pattern specification & body info first')
        return
    print('Simulating..')

    # Reload geometry in case something changed
    state.reload_garment()

    if state.garment.has_3D_intersections():
        result = cmds.confirmDialog(
            title='Confirm simulating with initial penetrations', 
            message='Garment either penetrates colliders or itself. Do you want to proceed with simulation?', 
            button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if result == 'No':
            return  # Do not start simulation

    mymaya.qualothwrapper.start_maya_sim(state.garment, state.config['sim'])

    # Update button 
    cmds.button(button, edit=True, 
                label='Stop Sim', backgroundColor=[245 / 256, 96 / 256, 66 / 256],
                command=partial(stop_sim_callback, button, state))


def stop_sim_callback(button, state, *args):
    """Stop simulation execution"""
    # toggle playback
    cmds.play(state=False)
    print('Simulation::Stopped')
    # uppdate button state
    cmds.button(button, edit=True, 
                label='Start Sim', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
                command=partial(start_sim_callback, button, state))


def win_closed_callback(*args):
    """Clean-up"""
    # Remove solver objects from the scene
    cmds.delete(cmds.ls('qlSolver*'))
    # Other created objects will be automatically deleted through destructors


def saving_folder_callback(view_field, state, *args):
    """Choose folder to save files to"""
    directory = cmds.fileDialog2(
        dialogStyle=2, 
        fileMode=3,  # directories 
        caption='Choose folder to save snapshots and renderings to'
    )
    if not directory:  # do nothing
        return 

    directory = directory[0]
    cmds.textField(view_field, edit=True, text=directory)

    state.save_to = directory

    # request saving prefix
    tag_result = cmds.promptDialog(
        t='Enter a saving prefix', 
        m='Enter a saving prefix:', 
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel'
    )
    if tag_result == 'OK':
        tag = cmds.promptDialog(query=True, text=True)
        state.saving_prefix = tag
    else:
        state.saving_prefix = None

    return True


def _new_dir(root_dir, tag='snap'):
    """create fresh directory for saving files"""
    folder = tag + '_' + datetime.now().strftime('%y%m%d-%H-%M-%S')
    path = os.path.join(root_dir, folder)
    os.makedirs(path)
    return path


def _create_saving_dir(view_field, state):
    """Try if saving is possible and create directory if yes"""
    if state.garment is None or state.scene is None:
        cmds.confirmDialog(title='Error', message='Load pattern specification & body info first')
        raise SceneSavingError('Scene is not ready')

    if state.save_to is None:
        if not saving_folder_callback(view_field, state):
            raise SceneSavingError('Saving folder not supplied')
    
    if state.saving_prefix is not None:
        tag = state.saving_prefix
    else: 
        tag = state.garment.name

    new_dir = _new_dir(state.save_to, tag)

    return new_dir


def quick_save_callback(view_field, state, *args):
    """Quick save with pattern spec and sim config"""
    try: 
        new_dir = _create_saving_dir(view_field, state)
    except SceneSavingError: 
        return 

    state.fetch()
    state.serialize(new_dir)

    print('Pattern spec and sim config saved to ' + new_dir)


def full_save_callback(view_field, state, *args):
    """Full save with pattern spec, sim config, garment mesh & rendering"""

    # do the same as for quick save
    try: 
        new_dir = _create_saving_dir(view_field, state)
    except SceneSavingError: 
        return 

    # save scene objects
    state.save_scene(new_dir)

    # save text properties
    state.fetch()
    state.serialize(new_dir)

    print('Pattern spec, props, 3D mesh & render saved to ' + new_dir)

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

import gc

# Maya
from maya import cmds
import maya.mel as mel

# My modules
import simulation as mysim
import customconfig
reload(mysim)
reload(customconfig)


class MayaGarmentWithUI(mysim.mayasetup.MayaGarment):
    """Extension of MayaGarment that can generate GUI for controlling the pattern"""
    def __init__(self, pattern_file, clean_on_die=False):
        super(MayaGarmentWithUI, self).__init__(pattern_file, clean_on_die)
        self.ui_top_layout = None
        self.ui_controls = {}
        # TODO - move to Parametrized class
        self.edge_dirs_list = [
            'start', 
            'end', 
            'both'
        ]
    
    def __del__(self):
        super(MayaGarmentWithUI, self).__del__()
        if self.ui_top_layout is not None:
            self._clean_layout(self.ui_top_layout)

    # ------- UI Drawing routines --------
    def drawUI(self, top_layout=None):
        """ Draw pattern controls in the given layout"""
        if top_layout is not None:
            self.ui_top_layout = top_layout
        if self.ui_top_layout is None:
            raise ValueError('GarmentDrawUI::top level layout not found')

        self._clean_layout(self.ui_top_layout)

        cmds.setParent(self.ui_top_layout)

        # Pattern name
        cmds.textFieldGrp(label='Pattern:', text=self.name, editable=False, 
                          cal=[1, 'left'], cw=[1, 50])

        # load panels info
        cmds.frameLayout(
            label='Panel Placement',
            collapsable=False, 
            borderVisible=True,
            mh=10, 
            mw=10
        )
        for panel in self.pattern['panels']:
            panel_layout = cmds.frameLayout(
                label=panel,
                collapsable=True, 
                collapse=True,
                borderVisible=True,
                mh=10, 
                mw=10
            )
            self._ui_3d_placement(self.pattern['panels'][panel]['translation'], [0, 0, 0])
            cmds.setParent('..')
        cmds.setParent('..')

        # Stitch info
        cmds.frameLayout(
            label='Stitches',
            collapsable=True, collapse=True,
            borderVisible=True,
            mh=10, mw=10
        )
        self._ui_stitches(self.pattern['stitches'])
        cmds.setParent('..')

        # Parameters
        cmds.frameLayout(
            label='Parameters',
            collapsable=False, borderVisible=True,
            mh=10, mw=10
        )
        self._ui_params(self.parameters, self.spec['parameter_order'])
        cmds.setParent('..')

        # fin
        cmds.setParent('..')
        
    def _clean_layout(self, layout):
        """Removes all of the childer from layout"""
        # TODO make static or move outside? 
        children = cmds.layout(layout, query=True, childArray=True)
        cmds.deleteUI(children)

    def _ui_3d_placement(self, transation, rotation):
        """Panel 3D position"""
        values = [0, 0, 0, 0]
        values[:len(transation)] = transation
        cmds.floatFieldGrp(
            label='Translation', 
            numberOfFields=len(transation), 
            value=values, 
            cal=[1, 'left'], cw=[1, 50]
        )

        values = [0, 0, 0, 0]
        values[:len(rotation)] = rotation
        cmds.floatFieldGrp(
            label='Rotation', 
            numberOfFields=len(rotation), 
            value=values, 
            cal=[1, 'left'], cw=[1, 50]
        )

    def _ui_stitches(self, stitches):
        """draw stitches UI"""
        cmds.gridLayout(numberOfColumns=6, enableKeyboardFocus=True, 
                        cellWidth=50)
        # header
        cmds.text(label='')
        cmds.text(label='Panel')
        cmds.text(label='Edge')
        cmds.text(label='')
        cmds.text(label='Panel')
        cmds.text(label='Edge')

        for idx, stitch in enumerate(stitches): 
            cmds.text(label='Stitch ' + str(idx))
            cmds.textField(text=stitch['from']['panel'], editable=False)
            cmds.intField(value=stitch['from']['edge'], editable=False)
            # ---
            cmds.text(label='To')
            cmds.textField(text=stitch['to']['panel'], editable=False)
            cmds.intField(value=stitch['to']['edge'], editable=False)
            # ----
            # TODO Add support for T-stitches
            # TODO Curve names instead of stitches? 
        
        # TODO add new stitch

        cmds.setParent('..')

    def _ui_params(self, params, order):
        """draw params UI"""
        # control
        cmds.button(
            label='To template state', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
            command=lambda *args: self._to_template_callback(), 
            ann='Snap all parameters to default values')

        # Parameters themselves
        for param_name in order:
            cmds.frameLayout(
                label=param_name, collapsable=True, collapse=True, mh=10, mw=10
            )
            # type 
            cmds.textFieldGrp(label='Type:', text=params[param_name]['type'], editable=False, 
                              cal=[1, 'left'], cw=[1, 30])

            # parameters might have multiple values
            values = params[param_name]['value']
            param_ranges = params[param_name]['range']
            if not isinstance(values, list):
                values = [values]
                param_ranges = [param_ranges]
            for idx, (value, param_range) in enumerate(zip(values, param_ranges)):
                # range 
                cmds.rowLayout(numberOfColumns=3)
                cmds.text(label='Range ' + str(idx) + ' info:')
                cmds.floatField(value=param_range[0], editable=False)
                cmds.floatField(value=param_range[1], editable=False)
                cmds.setParent('..')

                # value
                cmds.floatSliderGrp(
                    label='Value', field=True, value=value, 
                    minValue=param_range[0], maxValue=param_range[1], 
                    cal=[1, 'left'], cw=[1, 30]
                )

            # influence
            self._ui_param_influence(params[param_name]['influence'], params[param_name]['type'])
            # fin
            cmds.setParent('..')

    def _ui_param_influence(self, influence_list, type):
        """Draw UI for parameter influence"""
        cmds.frameLayout(
            label='Influence list',
            collapsable=False
        )
        cmds.gridLayout(numberOfColumns=3, enableKeyboardFocus=True, 
                        cellWidth=100, 
                        )
        # header
        cmds.text(label='Panel')
        cmds.text(label='Edge')
        cmds.text(label='Direction')

        for instance in influence_list:
            for edge in instance['edge_list']:
                cmds.textField(text=instance['panel'], editable=False)
                if type == 'length':
                    cmds.intField(value=edge['id'], editable=False)
                    self._quick_dropdown(self.edge_dirs_list, chosen=edge['direction'])
                else:
                    cmds.intField(value=edge, editable=False)
                    cmds.text(label='')

        cmds.setParent('..')
        cmds.setParent('..')

    def _quick_dropdown(self, options, chosen='', label=''):
        """Add a dropdown with given options"""
        menu = cmds.optionMenu(label=label)
        for option in options:
            cmds.menuItem(label=option)
        if chosen:
            cmds.optionMenu(menu, e=True, value=chosen)

        return menu

    # -------- Callbacks -----------
    def _to_template_callback(self):
        """Returns current pattern to template state and 
        updates UI accordingly"""
        # update
        print('Pattern returns to origins..')
        self._restore_template()
        # update UI in lazy manner
        self.drawUI()
        # update geometry in lazy manner
        if self.loaded_to_maya:
            self.load()


# ----- State -------
class State(object):
    def __init__(self):
        self.garment = None
        self.scene = None
        self.save_to = None
        self.body_file = None
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
    state.garment = MayaGarmentWithUI(template_file, True)  # previous object will autoclean
    state.garment.drawUI(state.pattern_layout)
    if state.scene is not None:
        state.garment.load(
            shader=state.scene.cloth_shader, 
            obstacles=[state.scene.body, state.scene.floor]
        )


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
    state.body_file = file
    state.scene = mysim.mayasetup.Scene(file, state.config['render'], clean_on_die=True)  # previous scene will autodelete
    if state.garment is not None:
        state.garment.load(
            shader=state.scene.cloth_shader, 
            obstacles=[state.scene.body, state.scene.floor]
        )
            

def load_props_callback(view_field, state):
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
    mysim.init_sim_props(state.config)  # fill the empty parts

    # Use current body info instead of one from config
    if state.body_file is not None:
        state.config['body'] = os.path.basename(state.body_file)

    # Update scene with new config
    if state.scene is not None:
        state.scene = mysim.mayasetup.Scene(
            state.body_file, state.config['render'], clean_on_die=True)  
        
        if state.garment is not None:
            state.garment.load(
                shader=state.scene.cloth_shader, 
                obstacles=[state.scene.body, state.scene.floor]
            )


def reload_garment_callback(state):
    """
        (re)loads current garment object to Maya if it exists
    """
    if state.garment is not None:
        state.garment.reloadJSON()
        state.garment.drawUI()  # update UI too 

        if state.scene is not None:
            state.garment.load(
                shader=state.scene.cloth_shader, 
                obstacles=[state.scene.body, state.scene.floor]
            )
    

def sim_callback(state):
    """ Start simulation """
    if state.garment is None or state.scene is None:
        cmds.confirmDialog(title='Error', message='Load pattern specification & body info first')
        return
    print('Simulating..')
    mysim.qw.qlCleanSimCache()

    # Reload geometry in case something changed
    state.garment.load(
        shader=state.scene.cloth_shader, 
        obstacles=[state.scene.body, state.scene.floor]
    )
    mysim.qw.start_maya_sim(state.garment, state.config['sim'])


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
        return False

    directory = directory[0]
    cmds.textField(view_field, edit=True, text=directory)

    state.save_to = directory
    return True


def _new_dir(root_dir, tag='snap'):
    """create fresh directory for saving files"""
    folder = tag + '_' + datetime.now().strftime('%y%m%d-%H-%M-%S')
    path = os.path.join(root_dir, folder)
    os.makedirs(path)
    return path


def quick_save_callback(view_field, state):
    """Quick save with pattern spec and sim config"""
    if state.save_to is None:
        if not saving_folder_callback(view_field, state):
            return ""
    
    new_dir = _new_dir(state.save_to, state.garment.name)

    # fetch props from maya -- updated global config
    state.scene.fetch_colors()
    # serialize
    state.config.serialize(os.path.join(new_dir, 'sim_props.json'))
    state.garment.serialize(new_dir, to_subfolder=False)

    print('Pattern spec and sim config saved to ' + new_dir)

    return new_dir


def full_save_callback(view_field, state):
    """Full save with pattern spec, sim config, garment mesh & rendering"""

    # do the same as for quick save
    new_dir = quick_save_callback(view_field, state)
    if not new_dir:
        return
    
    # save additional objects
    state.garment.save_mesh(new_dir)
    state.scene.render(new_dir)

    print('Pattern 3D mesh & render saved to ' + new_dir)


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


def text_button_group(callback, state, label='', button_label='Click'):
    """Custom version of textFieldButtonGrp"""
    cmds.rowLayout(nc=3, adj=2)
    cmds.text(label=label)
    text_field = cmds.textField(editable=False)
    cmds.button(
        label=button_label, 
        backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
        command=lambda *args: callback(text_field, state))
    cmds.setParent('..')
    return text_field


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
    # Pattern load
    text_button_group(template_field_callback, state, label='Pattern spec: ', button_label='Load')
    # body load
    text_button_group(load_body_callback, state, label='Body file: ', button_label='Load')
    # props load
    text_button_group(load_props_callback, state, label='Properties: ', button_label='Load')
    # separate
    cmds.separator()

    # Pattern description 
    state.pattern_layout = cmds.columnLayout(
        columnAttach=('both', 0), rowSpacing=main_offset, adj=1)
    filename_field = cmds.text(label='<pattern_here>', al='left')
    cmds.setParent('..')
    # separate
    cmds.separator()

    # Operations
    equal_rowlayout(2, win_width=window_width, offset=main_offset)
    cmds.button(label='Reload from JSON', backgroundColor=[255 / 256, 169 / 256, 119 / 256], 
                command=lambda *args: reload_garment_callback(state))
    cmds.button(label='Start Sim', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
                command=lambda *args: sim_callback(state))
    cmds.setParent('..')
    # separate
    cmds.separator()

    # Saving folder
    saving_to_field = text_button_group(saving_folder_callback, state, 
                                        label='Saving to: ', button_label='Choose')
    # saving requests
    equal_rowlayout(2, win_width=window_width, offset=main_offset)
    cmds.button(label='Save snapshot', backgroundColor=[227 / 256, 255 / 256, 119 / 256],
                command=lambda *args: quick_save_callback(saving_to_field, state), 
                ann='Quick save with pattern spec and sim config')
    cmds.button(label='Save with 3D', backgroundColor=[255 / 256, 140 / 256, 73 / 256], 
                command=lambda *args: full_save_callback(saving_to_field, state), 
                ann='Full save with pattern spec, sim config, garment mesh & rendering')
    cmds.setParent('..')

    # Last
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

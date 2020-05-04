"""
    Module for basic operations on patterns
    The code is compatible with both Python 2.7 (to be used in Maya 2020) and higher versions
"""
# Basic
from __future__ import print_function
import json
import numpy as np
import os

standard_names = [
    'specification',  # e.g. used by dataset generation
    'template', 
    'prediction'
]


class BasicPattern(object):
    """Loading & serializing of a pattern specification in custom JSON format.
        Input:
            * Pattern template in custom JSON format
        Output representations: 
            * Pattern instance in custom JSON format 
                * In the current state
        
        Not implemented: 
            * Convertion to NN-friendly format
            * Support for patterns with darts
    """

    # ------------ Interface -------------

    def __init__(self, pattern_file):

        self.spec_file = pattern_file
        self.path = os.path.dirname(pattern_file)
        self.name = os.path.splitext(os.path.basename(self.spec_file))[0]
        if self.name in standard_names:  # use name of directory instead
            self.name = os.path.basename(os.path.normpath(self.path))
        self.reloadJSON()

        self.parameter_types = [
            'length',
            'curve'
        ]

    def reloadJSON(self):
        """(Re)loads pattern info from spec file. 
        Useful when spec is updated from outside"""
        
        with open(self.spec_file, 'r') as f_json:
            self.spec = json.load(f_json)
        self.pattern = self.spec['pattern']
        self.parameters = self.spec['parameters']
        self.properties = self.spec['properties']  # mandatory part

        # template normalization - panel translations and curvature to relative coords
        self._normalize_template()

    def serialize(self, path, to_subfolder=True):
        # log context
        if to_subfolder:
            log_dir = os.path.join(path, self.name)
            os.makedirs(log_dir)
            spec_file = os.path.join(log_dir, 'specification.json')
        else:
            log_dir = path
            spec_file = os.path.join(path, (self.name + '_specification.json'))

        # Save specification
        with open(spec_file, 'w') as f_json:
            json.dump(self.spec, f_json, indent=2)
        
        return log_dir

    # --------- Pattern operations ----------
    def _normalize_template(self):
        """
        Updated template definition for convenient processing:
            * Converts curvature coordinates to realitive ones (in edge frame) -- for easy length scaling
            * snaps each panel to start at (0, 0)
        """
        if self.properties['curvature_coords'] == 'absolute':
            for panel in self.pattern['panels']:
                # convert curvature 
                vertices = self.pattern['panels'][panel]['vertices']
                edges = self.pattern['panels'][panel]['edges']
                for edge in edges:
                    if 'curvature' in edge:
                        edge['curvature'] = self._control_to_relative_coord(
                            vertices[edge['endpoints'][0]], 
                            vertices[edge['endpoints'][1]], 
                            edge['curvature']
                        )
            # now we have new property
            self.properties['curvature_coords'] = 'relative'
        
        # after curvature is converted!!
        # Only if requested
        if ('normalize_panel_translation' in self.properties 
                and self.properties['normalize_panel_translation']):
            print('Normalizing translation!')
            self.properties['normalize_panel_translation'] = False  # one-time use property. Preverts rotation issues on future reads
            for panel in self.pattern['panels']:
                # put origin in the middle of the panel-- 
                offset = self._normalize_panel_translation(panel)
                # udpate translation vector
                original = self.pattern['panels'][panel]['translation'] 
                self.pattern['panels'][panel]['translation'] = [
                    original[0] + offset[0], 
                    original[1] + offset[1], 
                    original[2], 
                ]

    def _normalize_panel_translation(self, panel_name):
        """ Convert panel vertices to local coordinates: 
            Shifts all panel vertices s.t. origin is at the center of the panel
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'])
        offset = np.mean(vertices, axis=0)
        vertices = vertices - offset

        panel['vertices'] = vertices.tolist()

        return offset
    
    def _control_to_abs_coord(self, start, end, control_scale):
        """
        Derives absolute coordinates of Bezier control point given as an offset
        """
        edge = end - start
        edge_perp = np.array([-edge[1], edge[0]])

        control_start = start + control_scale[0] * edge
        control_point = control_start + control_scale[1] * edge_perp

        return control_point 
    
    def _control_to_relative_coord(self, start, end, control_point):
        """
        Derives relative (local) coordinates of Bezier control point given as 
        a absolute (world) coordinates
        """
        start, end, control_point = np.array(start), np.array(end), \
            np.array(control_point)

        control_scale = [None, None]
        edge_vec = end - start
        edge_len = np.linalg.norm(edge_vec)
        control_vec = control_point - start
        
        # X
        # project control_vec on edge_vec by dot product properties
        control_projected_len = edge_vec.dot(control_vec) / edge_len 
        control_scale[0] = control_projected_len / edge_len
        # Y
        control_projected = edge_vec * control_scale[0]
        vert_comp = control_vec - control_projected  
        control_scale[1] = np.linalg.norm(vert_comp) / edge_len
        # Distinguish left&right curvature
        control_scale[1] *= np.sign(np.cross(control_point, edge_vec))

        return control_scale 

    def _edge_length(self, panel, edge):
        panel = self.pattern['panels'][panel]
        v_id_start, v_id_end = tuple(panel['edges'][edge]['endpoints'])
        v_start, v_end = np.array(panel['vertices'][v_id_start]), \
            np.array(panel['vertices'][v_id_end])
        
        return np.linalg.norm(v_end - v_start)
    
    # ---------- Parameters operations --------

    def _update_pattern_by_param_values(self):
        """
        Recalculates vertex positions and edge curves according to current
        parameter values
        (!) Assumes that the current pattern is a template:
                with all the parameters equal to defaults!
        """
        for parameter in self.spec['parameter_order']:
            value = self.parameters[parameter]['value']
            param_type = self.parameters[parameter]['type']
            if param_type not in self.parameter_types:
                raise ValueError("Incorrect parameter type. Alowed are "
                                 + self.parameter_types.keys())

            for panel_influence in self.parameters[parameter]['influence']:
                for edge in panel_influence['edge_list']:
                    if param_type == 'length':
                        self._extend_edge(panel_influence['panel'], edge, value)
                    elif param_type == 'curve':
                        self._curve_edge(panel_influence['panel'], edge, value)

    def _extend_edge(self, panel_name, edge_influence, scaling_factor):
        """
            Shrinks/elongates a given edge of a given panel. Applies equally
            to straight and curvy edges tnks to relative coordinates of curve controls
            Expects
                * each influenced edge to supply the elongatoin direction
                * scalar scaling_factor
        """
        if isinstance(scaling_factor, list):
            raise ValueError("Multiple scaling factors are not supported")

        panel = self.pattern['panels'][panel_name]
        v_id_start, v_id_end = tuple(
            panel['edges'][edge_influence["id"]]['endpoints'])
        v_start, v_end = np.array(panel['vertices'][v_id_start]), \
            np.array(panel['vertices'][v_id_end])

        # future edge    
        new_edge_vector = scaling_factor * (v_end - v_start)

        # apply extention in the appropriate direction
        if edge_influence["direction"] == 'end':
            v_end = v_start + new_edge_vector
        elif edge_influence["direction"] == 'start':
            v_start = v_end - new_edge_vector
        else:  # both
            v_middle = (v_start + v_end) / 2
            new_half_edge_vector = new_edge_vector / 2
            v_start, v_end = v_middle - new_half_edge_vector, \
                v_middle + new_half_edge_vector

        panel['vertices'][v_id_end] = v_end.tolist()
        panel['vertices'][v_id_start] = v_start.tolist()

    def _curve_edge(self, panel_name, edge, scaling_factor):
        """
            Updated the curvature of an edge accoding to scaling_factor.
            Can only be applied to edges with curvature information
            scaling_factor can be
                * scalar -- only the Y of control point is changed
                * 2-value list -- both coordinated of control are updated
        """
        panel = self.pattern['panels'][panel_name]
        if 'curvature' not in panel['edges'][edge]:
            raise ValueError('Applying curvature scaling to non-curvy edge '
                             + str(edge) + ' of ' + panel_name)
        control = panel['edges'][edge]['curvature']
        if isinstance(scaling_factor, list):
            control = [
                control[0] * scaling_factor[0],
                control[1] * scaling_factor[1]
            ]
        else:
            control[1] *= scaling_factor

        panel['edges'][edge]['curvature'] = control

    def _restore_template(self, params_to_default=True):
        """Restore pattern to it's state with all parameters having default values
            Recalculate vertex positions, edge curvatures & snap values to 1
        """
        # Follow the every order backwards
        for parameter in reversed(self.spec['parameter_order']):
            
            # invert value(s)
            inv_value = self.parameters[parameter]['value']
            try:  
                if isinstance(inv_value, list):
                    inv_value = map(lambda x: 1 / x, inv_value)
                else:
                    inv_value = 1 / inv_value
            except ZeroDivisionError as e:
                raise ZeroDivisionError('Zero value encountered while restoring template. Value is skipped')
            
            # Apply
            param_type = self.parameters[parameter]['type']
            if param_type not in self.parameter_types:
                raise ValueError("Incorrect parameter type. Alowed are "
                                 + self.parameter_types.keys())

            for panel_influence in reversed(self.parameters[parameter]['influence']):
                for edge in reversed(panel_influence['edge_list']):
                    if param_type == 'length':
                        self._extend_edge(panel_influence['panel'], edge, inv_value)
                    elif param_type == 'curve':
                        self._curve_edge(panel_influence['panel'], edge, inv_value)
            
            # restore defaults
            if params_to_default:
                if isinstance(inv_value, list):
                    self.parameters[parameter]['value'] = [1 for _ in inv_value]
                else:
                    self.parameters[parameter]['value'] = 1

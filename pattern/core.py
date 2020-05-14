"""
    Module for basic operations on patterns
    The code is compatible with both Python 2.7 (to be used in Maya 2020) and higher versions
"""
# Basic
from __future__ import print_function
from __future__ import division
import copy
import json
import numpy as np
import os
import random

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

    def reloadJSON(self):
        """(Re)loads pattern info from spec file. 
        Useful when spec is updated from outside"""
        
        with open(self.spec_file, 'r') as f_json:
            self.spec = json.load(f_json)
        self.pattern = self.spec['pattern']
        self.properties = self.spec['properties']  # mandatory part

        # template normalization - panel translations and curvature to relative coords
        self._normalize_template()

    def serialize(self, path, to_subfolder=True, tag=''):
        # log context
        if to_subfolder:
            log_dir = os.path.join(path, self.name + tag)
            os.makedirs(log_dir)
            spec_file = os.path.join(log_dir, 'specification.json')
        else:
            log_dir = path
            spec_file = os.path.join(path, (self.name + tag + '_specification.json'))

        # Save specification
        with open(spec_file, 'w') as f_json:
            json.dump(self.spec, f_json, indent=2)
        
        return log_dir

    def is_self_intersecting(self):
        """returns True if any of the pattern panels are self-intersecting"""
        return any(map(self._is_panel_self_intersecting, self.pattern['panels']))

    def _restore(self, backup_copy):
        """Restores spec structure from given backup copy 
            Makes a full copy of backup to avoid accidential corruption of backup
        """
        self.spec = copy.deepcopy(backup_copy)
        self.pattern = self.spec['pattern']
        self.properties = self.spec['properties']  # mandatory part

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

    # -------- Checks ------------
    def _is_panel_self_intersecting(self, panel_name):
        """Checks whatever a given panel contains intersecting edges
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.array(panel['vertices'])

        # construct edge list in coordinates
        edge_list = []
        for edge in panel['edges']:
            edge_ids = edge['endpoints']
            edge_coords = vertices[edge_ids]
            if 'curvature' in edge:
                curv_abs = self._control_to_abs_coord(edge_coords[0], edge_coords[1], edge['curvature'])
                # view curvy edge as two segments
                # NOTE this aproximation might lead to False positives in intersection tests
                edge_list.append([edge_coords[0], curv_abs])
                edge_list.append([curv_abs, edge_coords[1]])
            else:
                edge_list.append(edge_coords.tolist())

        # simple pairwise checks of edges
        # Follows discussion in  https://math.stackexchange.com/questions/80798/detecting-polygon-self-intersection 
        for i1 in range(0, len(edge_list)):
            for i2 in range(i1 + 1, len(edge_list)):
                if self._is_segm_intersecting(edge_list[i1], edge_list[i2]):
                    return True
        
        return False          
        
    def _is_segm_intersecting(self, segment1, segment2):
        """Checks wheter two segments intersect 
            in the points interior to both segments"""
        # https://algs4.cs.princeton.edu/91primitives/
        def ccw(start, end, point):
            """A test whether three points form counterclockwize angle (>0) 
            Returns (<0) if they form clockwize angle
            0 if collinear"""
            return (end[0] - start[0]) * (point[1] - start[1]) - (point[0] - start[0]) * (end[1] - start[1])

        # == 0 for edges sharing a vertex
        if (ccw(segment1[0], segment1[1], segment2[0]) * ccw(segment1[0], segment1[1], segment2[1]) >= 0
                or ccw(segment2[0], segment2[1], segment1[0]) * ccw(segment2[0], segment2[1], segment1[1]) >= 0):
            return False
        return True


class ParametrizedPattern(BasicPattern):
    """
        Extention to BasicPattern that can work with parametrized patterns
        Update pattern with new parameter values & randomize those parameters
    """
    def __init__(self, pattern_file):
        super(ParametrizedPattern, self).__init__(pattern_file)
        self.parameter_defaults = {
            'length': 1,
            'additive_length': 0,
            'curve': 1
        }

    def reloadJSON(self):
        """(Re)loads pattern info from spec file. 
        Useful when spec is updated from outside"""
        super(ParametrizedPattern, self).reloadJSON()
        self.parameters = self.spec['parameters']

    def _restore(self, backup_copy):
        """Restores spec structure from given backup copy 
            Makes a full copy of backup to avoid accidential corruption of backup
        """
        super(ParametrizedPattern, self)._restore(backup_copy)
        self.parameters = self.spec['parameters']
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
            if param_type not in self.parameter_defaults:
                raise ValueError("Incorrect parameter type. Alowed are "
                                 + self.parameter_defaults.keys())

            for panel_influence in self.parameters[parameter]['influence']:
                for edge in panel_influence['edge_list']:
                    if param_type == 'length':
                        self._extend_edge(panel_influence['panel'], edge, value)
                    elif param_type == 'additive_length':
                        self._extend_edge(panel_influence['panel'], edge, value, multiplicative=False)
                    elif param_type == 'curve':
                        self._curve_edge(panel_influence['panel'], edge, value)

    def _restore_template(self, params_to_default=True):
        """Restore pattern to it's state with all parameters having default values
            Recalculate vertex positions, edge curvatures & snap values to 1
        """
        # Follow the every order backwards
        for parameter in reversed(self.spec['parameter_order']):
            value = self.parameters[parameter]['value']
            param_type = self.parameters[parameter]['type']
            if param_type not in self.parameter_defaults:
                raise ValueError("Incorrect parameter type. Alowed are "
                                 + self.parameter_defaults.keys())

            for panel_influence in reversed(self.parameters[parameter]['influence']):
                for edge in reversed(panel_influence['edge_list']):
                    if param_type == 'length':
                        self._extend_edge(panel_influence['panel'], edge, self._invert_value(value))
                    elif param_type == 'additive_length':
                        self._extend_edge(panel_influence['panel'], edge, 
                                          self._invert_value(value, multiplicative=False), 
                                          multiplicative=False)
                    elif param_type == 'curve':
                        self._curve_edge(panel_influence['panel'], edge, self._invert_value(value))
            
            # restore defaults
            if params_to_default:
                if isinstance(value, list):
                    self.parameters[parameter]['value'] = [self.parameter_defaults[param_type] for _ in value]
                else:
                    self.parameters[parameter]['value'] = self.parameter_defaults[param_type]

    def _extend_edge(self, panel_name, edge_influence, value, multiplicative=True):
        """
            Shrinks/elongates a given edge or edge collection of a given panel. Applies equally
            to straight and curvy edges tnks to relative coordinates of curve controls
            Expects
                * each influenced edge to supply the elongatoin direction
                * scalar scaling_factor
            'multiplicative' parameter controls the type of extention:
                * if True, value is treated as a scaling factor of the edge or edge projection -- default
                * if False, value is added to the edge or edge projection
        """
        if isinstance(value, list):
            raise ValueError("Multiple scaling factors are not supported")

        panel = self.pattern['panels'][panel_name]

        if isinstance(edge_influence["id"], list):
            # meta-edge
            # get all vertices in order
            verts_ids = [panel['edges'][edge_influence['id'][0]]['endpoints'][0]]  # start
            for edge_id in edge_influence['id']:
                verts_ids.append(panel['edges'][edge_id]['endpoints'][1])  # end vertices
        else:
            # single edge
            verts_ids = panel['edges'][edge_influence['id']]['endpoints']

        verts_coords = []
        for idx in verts_ids:
            verts_coords.append(panel['vertices'][idx])
        verts_coords = np.array(verts_coords)

        # calc extention pivot
        if edge_influence['direction'] == 'end':
            fixed = verts_coords[0]  # start is fixed
        elif edge_influence['direction'] == 'start':
            fixed = verts_coords[-1]  # end is fixed
        else:  # both
            fixed = (verts_coords[0] + verts_coords[-1]) / 2

        # calc extention line
        if 'along' in edge_influence:
            target_line = edge_influence['along']
        else:
            target_line = verts_coords[-1] - verts_coords[0] 

        if np.isclose(np.linalg.norm(target_line), 0):
            raise ZeroDivisionError('target line is zero ' + str(target_line))
        else:
            target_line /= np.linalg.norm(target_line)

        # move verts 
        # * along target line that sits on fixed point (correct sign & distance along the line)
        verts_projection = np.empty(verts_coords.shape)
        for i in range(verts_coords.shape[0]):
            verts_projection[i] = (verts_coords[i] - fixed).dot(target_line) * target_line

        if multiplicative:
            # * to match the scaled projection (correct point of application -- initial vertex position)
            new_verts = verts_coords - (1 - value) * verts_projection
        else:
            # * to match the added projection: 
            # still need projection to make sure the extention derection is corect relative to fixed point
            
            # normalize first
            for i in range(verts_coords.shape[0]):
                norm = np.linalg.norm(verts_projection[i])
                if not np.isclose(norm, 0):
                    verts_projection[i] /= norm

            # zero projections were not normalized -- they will zero-out the effect
            new_verts = verts_coords + value * verts_projection

        # update in the initial structure
        for ni, idx in enumerate(verts_ids):
            panel['vertices'][idx] = new_verts[ni].tolist()

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

    def _invert_value(self, value, multiplicative=True):
        """If value is a list, return a list with each value inverted.
            'multiplicative' parameter controls the type of inversion:
                * if True, returns multiplicative inverse (1/value) == default
                * if False, returns additive inverse (-value)
        """
        if multiplicative:
            if isinstance(value, list):
                if any(np.isclose(value), 0):
                    raise ZeroDivisionError('Zero value encountered while restoring multiplicative parameter.')
                return map(lambda x: 1 / x, value)
            else:
                if np.isclose(value, 0):
                    raise ZeroDivisionError('Zero value encountered while restoring multiplicative parameter.')
                return 1 / value
        else:
            if isinstance(value, list):
                return map(lambda x: -x, value)
            else:
                return -value

    # ---------- Randomization -
    def _new_value(self, param_range):
        """Random value within range given as an iteratable"""
        value = random.uniform(param_range[0], param_range[1])
        # prevent non-reversible zero values
        if abs(value) < 1e-2:
            value = 1e-2 * (-1 if value < 0 else 1)
        return value

    def _randomize_parameters(self):
        """
        Sets new random values for the pattern parameters
        Parameter type agnostic
        """
        for parameter in self.parameters:
            param_ranges = self.parameters[parameter]['range']

            # check if parameter has multiple values (=> multiple ranges) like for curves
            if isinstance(self.parameters[parameter]['value'], list): 
                values = []
                for param_range in param_ranges:
                    values.append(self._new_value(param_range))
                self.parameters[parameter]['value'] = values
            else:  # simple 1-value parameter
                self.parameters[parameter]['value'] = self._new_value(param_ranges)

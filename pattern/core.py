"""
    Module for basic operations on patterns
    The code is compatible with both Python 2.7 (to be used in Maya 2020) and higher versions
"""
# Basic
from __future__ import print_function
import json
import numpy as np
import os


class BasicPattern(object):
    """
        Loading & serializing of a pattern specification in custom JSON format.
        Input:
            * Pattern template in custom JSON format
        Output representations: 
            * Pattern instance in custom JSON format 
                * In the current state
        
        Not implemented: 
            * Convertion to NN-friendly format
            * Support for patterns with darts
            * Convertion to Simulatable format
            * Panel positioning
    """

    # ------------ Interface -------------

    def __init__(self, pattern_file):

        self.spec_file = pattern_file
        self.path = os.path.dirname(pattern_file)
        self.name = os.path.basename(self.spec_file)
        self.name = os.path.splitext(self.name)[0]

        with open(pattern_file, 'r') as f_json:
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
        for panel in self.pattern['panels']:
            if self.properties['curvature_coords'] == 'absolute':
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
            # normalize tranlsation after curvature is converted!
            # UPD Do not normalize tranlsation on loading
            # TODO finalize after proper 3D placement
            # self._normalize_panel_translation(panel)
        # now we have new property
        self.properties['curvature_coords'] = 'relative'

    def _normalize_panel_translation(self, panel_name):
        """
        DEPRECATED TODO update or remove after finalizinf 3D positioning
        Shifts all panel vertices s.t. panel bounding box starts at zero
        for uniformity across panels & positive coordinates
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'])
        offset = np.min(vertices, axis=0)
        vertices = vertices - offset

        panel['vertices'] = vertices.tolist()
    
    def _control_to_abs_coord(self, start, end, control_scale):
        """
        Derives absolute coordinates of Bezier control point given as an offset
        """
        control_start = control_scale[0] * (start + end)

        edge = end - start
        edge_perp = np.array([-edge[1], edge[0]])
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

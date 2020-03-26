# For wrapper
import json
import svgwrite
from svglib import svglib
from reportlab.graphics import renderPM
import numpy as np
import random
import string
from pathlib import Path
import os

# for main only
from datetime import datetime
import time


class PatternWrapper():
    """
        Loading, represenation convertion, parameter randomization of a pattern template
        in custom JSON format.
        Input:
            * Pattern template in custom JSON format
        Output representations: 
            * Pattern instance in custom JSON format 
                (with updated parameter values and vertex positions)
            * SVG (stitching info is lost)
            * PNG for visualization

        Implementation limitations: 
            * Parameter randomization is only performed once on loading
            * Only accepts unchanged template files (all parameter values = 1) 
            otherwise, parameter values will go out of control and outside of the original range
            (with no way to recognise it)
        
        Not implemented: 
            * Convertion to NN-friendly format
            * Support for patterns with darts
            * Convertion to Simulatable format
            * Panel positioning
    """

    # ------------ Interface -------------

    def __init__(self, template_file, randomize=""):

        self.template_file = Path(template_file)
        self.name = self.__get_name(self.template_file.stem, randomize)

        with open(template_file, 'r') as f_json:
            self.template = json.load(f_json)
        self.pattern = self.template['pattern']
        self.parameters = self.template['parameters']

        self.scaling_for_drawing = self.__verts_to_px_scaling_factor()

        # randomization setup
        self.parameter_processors = {
            'length': self.__extend_edge,
            'curve': self.__curve_edge
        }

        if randomize:
            self.__randomize_parameters()
            self.__update_pattern_by_param_values()

    def serialize(self, path, to_subfolder=True):
        # log context
        if to_subfolder:
            log_dir = Path(path) / self.name
            os.makedirs(log_dir)
            spec_file = log_dir / 'specification.json'
            svg_file = log_dir / 'pattern.svg'
            png_file = log_dir / 'pattern.png'
        else:
            spec_file = Path(path) / (self.name + '_specification.json')
            svg_file = Path(path) / (self.name + '_pattern.svg')
            png_file = Path(path) / (self.name + '_pattern.png')

        # Save specification
        with open(spec_file, 'w') as f_json:
            json.dump(self.template, f_json, indent=2)
        # visualtisation
        self.__save_as_image(svg_file, png_file)

    # --------- Pattern operations ----------
    @staticmethod
    def __new_value(param_range):
        """Random value within range given as an iteratable"""
        return random.uniform(param_range[0], param_range[1])

    def __randomize_parameters(self):
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
                    values.append(PatternWrapper.__new_value(param_range))
                self.parameters[parameter]['value'] = values
            else:  # simple 1-value parameter
                self.parameters[parameter]['value'] = PatternWrapper.__new_value(param_ranges)

    def __update_pattern_by_param_values(self):
        """
        Recalculates vertex positions and edge curves according to current
        parameter values
        (!) Assumes that the current pattern is a template:
                was created with all the parameters equal to 1
        """
        # Edge length adjustments
        for parameter in self.template['parameter_order']:
            value = self.parameters[parameter]['value']
            param_type = self.parameters[parameter]['type']
            if param_type not in self.parameter_processors:
                raise ValueError("Incorrect parameter type. Alowed are "
                                 + self.parameter_processors.keys())

            for panel_influence in self.parameters[parameter]['influence']:
                for edge in panel_influence['edge_list']:
                    self.parameter_processors[param_type](
                        panel_influence['panel'], edge, value)

                self.__normalize_panel_translation(panel_influence['panel'])
        
        # print(self.name, self.__edge_length('front', 0), self.__edge_length('back', 0))

    # -------- Updating edges by parameters ---------

    def __extend_edge(self, panel_name, edge_influence, scaling_factor):
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

    def __curve_edge(self, panel_name, edge, scaling_factor):
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

    # -------- Pattern utils ---------

    def __normalize_panel_translation(self, panel_name):
        """
        Shifts all panel vertices s.t. panel bounding box starts at zero
        for uniformity across panels & positive coordinates
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'])
        offset = np.min(vertices, axis=0)
        vertices = vertices - offset

        panel['vertices'] = vertices.tolist()
    
    def __calc_control_coord(self, start, end, control_scale):
        """
        Derives absolute coordinates of Bezier control point given as an offset
        """
        control_start = control_scale[0] * (start + end)

        edge = end - start
        edge_perp = np.array([-edge[1], edge[0]])
        control_point = control_start + control_scale[1] * edge_perp

        return control_point 

    def __edge_length(self, panel, edge):
        panel = self.pattern['panels'][panel]
        v_id_start, v_id_end = tuple(panel['edges'][edge]['endpoints'])
        v_start, v_end = np.array(panel['vertices'][v_id_start]), \
            np.array(panel['vertices'][v_id_end])
        
        return np.linalg.norm(v_end - v_start)

    # -------- Drawing ---------

    def __verts_to_px_scaling_factor(self):
        """
        Estimates multiplicative factor to convert vertex units to pixel coordinates
        Heuritic approach, s.t. all the patterns from the same template are displayed similarly
        """
        any_panel = next(iter(self.pattern['panels'].values()))
        vertices = np.asarray(any_panel['vertices'])

        box_size = np.max(vertices, axis=0) - np.min(vertices, axis=0) 
        if box_size[0] < 2:      # meters
            scaling_to_px = 200
        elif box_size[0] < 200:  # sentimeters
            scaling_to_px = 2
        else:                    # pixels
            scaling_to_px = 1  

        return scaling_to_px

    def ___draw_a_panel(self, drawing, panel_name, offset=[0, 0], scaling=1):
        """
        Adds a requested panel to the svg drawing with given offset and scaling
        Assumes (!!) 
            that edges are correctly oriented to form a closed loop
        Returns 
            the lower-right vertex coordinate for the convenice of future offsetting.
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'], dtype=int)

        # Scale & shift vertices for visibility
        vertices = vertices * scaling + offset

        # draw
        start = vertices[panel['edges'][0]['endpoints'][0]]
        path = drawing.path(['M', start[0], start[1]],
                            stroke='black', fill='rgb(255,217,194)')
        for edge in panel['edges']:
            # TODO add darts visualization here!
            start = vertices[edge['endpoints'][0]]
            end = vertices[edge['endpoints'][1]]
            if ('curvature' in edge):
                control_scale = edge['curvature']
                control_point = self.__calc_control_coord(
                    start, end, control_scale)
                path.push(
                    ['Q', control_point[0], control_point[1], end[0], end[1]])
            else:
                path.push(['L', end[0], end[1]])
        path.push('z')  # path finished
        drawing.add(path)

        # name the panel
        panel_center = np.mean(vertices, axis=0)
        drawing.add(drawing.text(panel_name, insert=panel_center, fill='blue'))

        return np.max(vertices[:, 0]), np.max(vertices[:, 1])

    def __save_as_image(self, svg_filename, png_filename):
        """Saves current pattern in svg and png format for visualization"""

        dwg = svgwrite.Drawing(svg_filename.as_posix(), profile='tiny')
        base_offset = [40, 40]
        panel_offset = [0, 0]
        for panel in self.pattern['panels']:
            panel_offset = self.___draw_a_panel(
                dwg, panel,
                offset=[panel_offset[0] + base_offset[0], base_offset[1]],
                scaling=self.scaling_for_drawing)

        # final sizing & save
        dwg['width'] = str(panel_offset[0] + base_offset[0]) + 'px'
        dwg['height'] = str(panel_offset[1] + base_offset[1]) + 'px'
        dwg.save(pretty=True)

        # to png
        svg_pattern = svglib.svg2rlg(svg_filename.as_posix())
        renderPM.drawToFile(svg_pattern, png_filename, fmt='png')

    # -------- Other Utils ---------

    def __id_generator(self, size=10,
                       chars=string.ascii_uppercase + string.digits):
        """Generated a random string of a given size, see
        https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
        """
        return ''.join(random.choices(chars, k=size))

    def __get_name(self, prefix, randomize):
        name = prefix
        if randomize:
            name = name + '_' + self.__id_generator()
        return name


if __name__ == "__main__":

    timestamp = int(time.time())
    random.seed(timestamp)

    base_path = Path('F:/GK-Pattern-Data-Gen/')
    pattern = PatternWrapper(Path('./Patterns') / 'skirt_per_panel.json',
                             randomize=False)
    # print (pattern.pattern['panels'])

    # log to file
    log_folder = 'base_skirt_per_panel_' + datetime.now().strftime('%y%m%d-%H-%M')
    os.makedirs(base_path / log_folder)

    pattern.serialize(base_path / log_folder, to_subfolder=False)

    # log random seed
    with open(base_path / log_folder / 'random_seed.txt', 'w') as f_rand:
        f_rand.write(str(timestamp))

"""
    Adapted to be used in Python 3.6+
    TODO It might make sence to turn drawing into routines rather then new class
"""
import svgwrite
from svglib import svglib
from reportlab.graphics import renderPM
import random
import string
import os
import numpy as np

# my -- the construction is needed to run this module with __main__
# See https://stackoverflow.com/questions/8299270/ultimate-answer-to-relative-python-imports
if __name__ == '__main__':
    import os
    import sys
    # get an absolute path to the directory that contains mypackage
    curr_dir = os.path.dirname(os.path.join(os.getcwd(), __file__))
    sys.path.append(os.path.normpath(os.path.join(curr_dir, '..', '..')))
    from pattern import core
else:
    from . import core


class VisPattern(core.BasicPattern):
    """
        "Visualizible" pattern wrapper of pattern specification in custom JSON format.
        Input:
            * Pattern template in custom JSON format
        Output representations: 
            * Pattern instance in custom JSON format 
                * In the current state
            * SVG (stitching info is lost)
            * PNG for visualization
        
        Not implemented: 
            * Support for patterns with darts
    """

    # ------------ Interface -------------

    def __init__(self, pattern_file):
        super().__init__(pattern_file)

        # tnx to this all patterns produced from the same template will have the same 
        # visualization scale
        # and that's why I need a class object fot 
        self.scaling_for_drawing = self._verts_to_px_scaling_factor()

    def serialize(self, path, to_subfolder=True):

        log_dir = super().serialize(path, to_subfolder)
        if to_subfolder:
            svg_file = os.path.join(log_dir, 'pattern.svg')
            png_file = os.path.join(log_dir, 'pattern.png')
        else:
            svg_file = os.path.join(log_dir, (self.name + '_pattern.svg'))
            png_file = os.path.join(log_dir, (self.name + '_pattern.png'))

        # save visualtisation
        self._save_as_image(svg_file, png_file)

    # -------- Drawing ---------

    def _verts_to_px_scaling_factor(self):
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

    def _verts_to_px_coords(self, vertices):
        """Convert given to px coordinate frame & units"""
        # Flip Y coordinate (in SVG Y looks down)
        vertices[:, 1] *= -1
        # Put upper left corner of the bounding box at zero
        offset = np.min(vertices, axis=0)
        vertices = vertices - offset
        # Update units scaling
        vertices *= self.scaling_for_drawing
        return vertices

    def _flip_y(self, point):
        """
            To get to image coordinates one might need to flip Y axis
        """
        point[1] *= -1
        return point

    def _draw_a_panel(self, drawing, panel_name, offset=[0, 0]):
        """
        Adds a requested panel to the svg drawing with given offset and scaling
        Assumes (!!) 
            that edges are correctly oriented to form a closed loop
        Returns 
            the lower-right vertex coordinate for the convenice of future offsetting.
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'], dtype=int)
        vertices = self._verts_to_px_coords(vertices)
        # Shift vertices for visibility
        vertices = vertices + offset

        # draw
        start = vertices[panel['edges'][0]['endpoints'][0]]
        path = drawing.path(['M', start[0], start[1]],
                            stroke='black', fill='rgb(255,217,194)')
        for edge in panel['edges']:
            # TODO add darts visualization here!
            start = vertices[edge['endpoints'][0]]
            end = vertices[edge['endpoints'][1]]
            if ('curvature' in edge):
                control_scale = self._flip_y(edge['curvature'])
                control_point = self._control_to_abs_coord(
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

    def _save_as_image(self, svg_filename, png_filename):
        """Saves current pattern in svg and png format for visualization"""

        dwg = svgwrite.Drawing(svg_filename, profile='tiny')
        base_offset = [40, 40]
        panel_offset = [0, 0]
        for panel in self.pattern['panels']:
            panel_offset = self._draw_a_panel(
                dwg, panel,
                offset=[panel_offset[0] + base_offset[0], base_offset[1]]
            )

        # final sizing & save
        dwg['width'] = str(panel_offset[0] + base_offset[0]) + 'px'
        dwg['height'] = str(panel_offset[1] + base_offset[1]) + 'px'
        dwg.save(pretty=True)

        # to png
        svg_pattern = svglib.svg2rlg(svg_filename)
        renderPM.drawToFile(svg_pattern, png_filename, fmt='png')


class RandomPattern(VisPattern):
    """
        Parameter randomization of a pattern template in custom JSON format.
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
    """

    # ------------ Interface -------------
    def __init__(self, template_file):
        super().__init__(template_file)

        # update name for a random pattern
        self.name = self.name + '_' + self._id_generator()

        # randomization setup
        self.parameter_processors = {
            'length': self._extend_edge,
            'curve': self._curve_edge
        }
        self._randomize_parameters()
        self._update_pattern_by_param_values()

    # --------- Updating pattern by new values  ----------

    def _new_value(self, param_range):
        """Random value within range given as an iteratable"""
        return random.uniform(param_range[0], param_range[1])

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

    def _update_pattern_by_param_values(self):
        """
        Recalculates vertex positions and edge curves according to current
        parameter values
        (!) Assumes that the current pattern is a template:
                was created with all the parameters equal to 1
        """
        # Edge length adjustments
        for parameter in self.spec['parameter_order']:
            value = self.parameters[parameter]['value']
            param_type = self.parameters[parameter]['type']
            if param_type not in self.parameter_processors:
                raise ValueError("Incorrect parameter type. Alowed are "
                                 + self.parameter_processors.keys())

            for panel_influence in self.parameters[parameter]['influence']:
                for edge in panel_influence['edge_list']:
                    self.parameter_processors[param_type](
                        panel_influence['panel'], edge, value)

                # super()._normalize_panel_translation(panel_influence['panel'])
        
        # print(self.name, self.__edge_length('front', 0), self.__edge_length('back', 0))

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

    # -------- Other Utils ---------

    def _id_generator(self, size=10,
                      chars=string.ascii_uppercase + string.digits):
        """Generated a random string of a given size, see
        https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
        """
        return ''.join(random.choices(chars, k=size))


if __name__ == "__main__":
    from datetime import datetime
    import time

    timestamp = int(time.time())
    random.seed(timestamp)

    base_path = 'F:/GK-Pattern-Data-Gen/'
    pattern = VisPattern('./Patterns/skirt_maya_coords.json')
    newpattern = RandomPattern('./Patterns/skirt_maya_coords.json')

    # log to file
    log_folder = 'coords_flip_' + datetime.now().strftime('%y%m%d-%H-%M')
    log_folder = os.path.join(base_path, log_folder)
    os.makedirs(log_folder)

    pattern.serialize(log_folder, to_subfolder=False)
    newpattern.serialize(log_folder, to_subfolder=False)

    # log random seed
    with open(log_folder + '/random_seed.txt', 'w') as f_rand:
        f_rand.write(str(timestamp))

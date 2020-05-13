"""
    Adapted to be used in Python 3.6+
    TODO It might make sence to turn drawing into routines rather then new class
"""
import copy
import random
import string
import os
import numpy as np

import svgwrite
from svglib import svglib
from reportlab.graphics import renderPM

# my
import customconfig
from pattern import core


class VisPattern(core.ParametrizedPattern):
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

    def __init__(self, pattern_file, view_ids=True):
        super().__init__(pattern_file)

        # tnx to this all patterns produced from the same template will have the same 
        # visualization scale
        # and that's why I need a class object fot 
        self.scaling_for_drawing = self._verts_to_px_scaling_factor()
        self.view_ids = view_ids  # whatever to render vertices & endes indices

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

        # draw edges
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
        drawing.add(drawing.text(panel_name, insert=panel_center + np.array([-25, 3]), 
                    fill='rgb(9,33,173)', font_size='25'))

        if self.view_ids:
            # name vertices 
            for idx in range(vertices.shape[0]):
                shift = vertices[idx] - panel_center
                # last element moves pivot to digit center
                shift = 5 * shift / np.linalg.norm(shift) + np.array([-5, 5])
                drawing.add(
                    drawing.text(str(idx), insert=vertices[idx] + shift, 
                                 fill='rgb(245,96,66)', font_size='25'))
            # name edges
            for idx, edge in enumerate(panel['edges']):
                middle = np.mean(
                    vertices[[edge['endpoints'][0], edge['endpoints'][1]]], axis=0)
                shift = middle - panel_center
                shift = 5 * shift / np.linalg.norm(shift) + np.array([-5, 5])
                # name
                drawing.add(
                    drawing.text(idx, insert=middle + shift, 
                                 fill='rgb(50,179,101)', font_size='20'))

        return np.max(vertices[:, 0]), np.max(vertices[:, 1])

    def _save_as_image(self, svg_filename, png_filename):
        """
            Saves current pattern in svg and png format for visualization
        """

        dwg = svgwrite.Drawing(svg_filename, profile='tiny')
        base_offset = [60, 60]
        panel_offset_x = 0
        heights = []
        for panel in self.pattern['panels']:
            panel_offset_x, height = self._draw_a_panel(
                dwg, panel,
                offset=[panel_offset_x + base_offset[0], base_offset[1]]
            )
            heights.append(height)

        # final sizing & save
        dwg['width'] = str(panel_offset_x + base_offset[0]) + 'px'  # using latest offset -- the most right
        dwg['height'] = str(max(heights) + base_offset[1]) + 'px'
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
        super().__init__(template_file, view_ids=False)  # don't show ids for datasets

        # update name for a random pattern
        self.name = self.name + '_' + self._id_generator()

        # randomization setup
        self._randomize()

    def _randomize(self):
        """Robustly randomize current pattern"""

        spec_backup = copy.deepcopy(self.spec)
        self._randomize_parameters()
        self._update_pattern_by_param_values()
        for tries in range(100):  # upper bound on trials to avoid infinite loop
            if not self.is_self_intersecting():
                break

            print('Warning::Randomized pattern is self-intersecting. Re-try..')
            self._restore(spec_backup)
            # Try again
            self._randomize_parameters()
            self._update_pattern_by_param_values()

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

    system_config = customconfig.Properties('../system.json')
    base_path = system_config['output']
    # pattern = VisPattern(os.path.join(system_config['templates_path'], 'basic tee', 'tee.json'))
    pattern = VisPattern(os.path.join(base_path, 't-data_tee_200507-14-01-01', 'tee_4F0L01ONR5_specification.json'))
    newpattern = RandomPattern(os.path.join(system_config['templates_path'], 'basic tee', 'tee.json'))

    # log to file
    log_folder = 'intersect_' + datetime.now().strftime('%y%m%d-%H-%M-%S')
    log_folder = os.path.join(base_path, log_folder)
    os.makedirs(log_folder)

    pattern.serialize(log_folder, to_subfolder=False)
    newpattern.serialize(log_folder, to_subfolder=False)

    # log random seed
    with open(log_folder + '/random_seed.txt', 'w') as f_rand:
        f_rand.write(str(timestamp))

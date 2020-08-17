# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Stylesheet for timeline drawer.
"""
import dataclasses
from typing import Callable

from qiskit.visualization.timeline import macros


@dataclasses.dataclass
class QiskitTimelineStyle:
    """Qiskit standard stylesheet for timeline drawer.
    """

    #################################
    # Gate appearance
    #
    # There are two types of gates:
    # (1) box-type with finite duration and (2) dot-type with zero duration.
    # Those gates have some independent styling fields.
    #################################

    # height of gate box
    gate_height: float = 0.5

    # layer index of gate box, large index comes front
    gate_box_z_order = 3

    # layer index of gate dot, large index comes front
    gate_dot_z_order = 4

    # transparency of gate (common for box and dot)
    gate_alpha: float = 0.9

    # size of gate dot
    gate_dot_marker_size: float = 30.

    # length of constriction on both sides of gate box
    gate_box_side_width: float = 4.

    # edge color of gate box
    gate_box_edge_color: str = None

    # edge color of gate dot
    gate_dot_edge_color: str = '#000000'

    # text color of gate (common for box and dot)
    gate_text_color: str = '#000000'

    # front text size of gate (common for box and dot)
    gate_text_size: int = 60

    #################################
    # Barrier appearance
    #
    #################################

    # layer index of barrier, large index comes front
    barrier_z_order: int = 2

    # line width of barrier
    barrier_linewidth: float = 5.

    # line color of barrier
    barrier_color: str = '#BBBBBB'

    # transparency of barrier
    barrier_alpha: float = 1.

    # line style of barrier, conform to matplotlib linestyle
    barrier_line_style: str = '-'

    #################################
    # Register link appearance
    #
    # Multi-register instruction are drawn with a line between registers.
    #################################

    # layer index of register link, large index comes front
    link_z_order: int = 2

    # minimum horizontal spacing of register links
    # if two register links are placed within this distance,
    # those horizontal position is shifted to keep the margin specified here
    link_h_spacing: float = 20.

    # line width of register link
    link_linewidth: float = 100.

    # transparency of register link
    link_alpha: float = 0.7

    # marker type of register link, conform to matplotlib marker
    link_marker: str = None

    #################################
    # Timeline appearance
    #
    # Gates are drawn on this belt of timeline.
    #################################

    # layer index of timeline, large index comes front
    timeline_z_order: int = 1

    # transparency of timeline
    timeline_alpha: float = 0.7

    # face color of timeline
    timeline_facecolor: str = '#DDDDDD'

    # edge color of timeline
    timeline_edgecolor: str = None

    #################################
    # Register label appearance
    #
    #################################

    # layer index of register label, large index comes front
    register_label_z_order: int = 4

    # horizontal offset from the left edge of timeline belt
    register_label_h_offset: float = 5.

    # font size of register label
    register_label_fontsize: int = 18

    #################################
    # Drawing options
    #
    #################################

    # set True to show register links
    show_multi_qubit_link: bool = True

    # set True to show initial qubit state |0> after register name
    show_initial_state: bool = False

    #################################
    # Active controls
    #
    # Set of callback function to control drawing objects.
    #################################

    # get systematic gate name and returns corresponding color code
    gate_color_mapper: Callable = macros.get_iqx_gate_color

    # get systematic gate name and format it
    gate_name_mapper: Callable = macros.get_latex_gate_name

    #################################
    # Canvas format
    #
    # General setup of drawing canvas.
    #################################

    # vertical canvas size per register in units of inch
    canvas_inch_per_unit_v = 8

    # horizontal canvas size per dt in units of inch
    canvas_inch_per_unit_h = 0.06

    # dot per inch when save output figure in file
    save_dpi = 150

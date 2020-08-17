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
"""
Macros for timeline drawer.
Those macros are bound to :py:class:`~qiskit.visualization.timeline.style.QiskitTimelineStyle`.
Use can write own callback function and replace one in the stylesheet to
fine tune the output image.
"""


def get_iqx_gate_color(name: str) -> str:
    """Returns color code for given gate based on IQX composer.
    """
    color_dict = {
        'u0': '#FA74A6',
        'u1': '#33B1FF',
        'u2': '#FA4D56',
        'u3': '#FA4D56',
        'id': '#05BAB6',
        'x': '#05BAB6',
        'xp': '#01796F',
        'xm': '#01796F',
        'y': '#05BAB6',
        'z': '#05BAB6',
        'h': '#6FA4FF',
        'cx': '#002D9C',
        'cy': '#6FA4FF',
        'cz': '#6FA4FF',
        'swap': '#6FA4FF',
        's': '#6FA4FF',
        'sdg': '#6FA4FF',
        'dcx': '#6FA4FF',
        'iswap': '#6FA4FF',
        't': '#BB8BFF',
        'tdg': '#BB8BFF',
        'r': '#BB8BFF',
        'rx': '#BB8BFF',
        'ry': '#BB8BFF',
        'rz': '#BB8BFF',
        'reset': '#000000',
        'target': '#FFFFFF',
        'multi': '#BB8BFF',
        'measure': '#000000',
        'delay': '#58555c'
    }

    return color_dict.get(name, '#BB8BFF')


def get_latex_gate_name(name: str) -> str:
    """Returns gate name in LaTex representation.
    """
    name_dict = {
        'u0': r'U$_0$',
        'u1': r'',
        'u2': r'U$_2$',
        'u3': r'U$_3$',
        'id': r'Id',
        'x': r'X',
        'y': r'Y',
        'z': r'Z',
        'h': r'H',
        'cx': r'CX',
        'cy': r'CY',
        'cz': r'CZ',
        'swap': r'SWAP',
        's': r'S',
        'sdg': r'S$^\dagger$',
        'dcx': r'DCX',
        'iswap': r'iSWAP',
        't': r'T',
        'tdg': r'T$^\dagger$',
        'r': r'R',
        'rx': r'R$_x$',
        'ry': r'R$_y$',
        'rz': r'R$_z$',
        'reset': r'$|0\rangle$',
        'target': r'Target',
        'multi': r'Multi',
        'measure': r'Measure'
    }

    return name_dict.get(name, name)

# -*- coding: utf-8 -*-

# (C) Copyright Ji Liu and Luciano Bello, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Non-entangled state annotation
"""
#from qiskit.circuit import ControlledGate
from qiskit.circuit import Gate
from qiskit.circuit import QuantumRegister
import numpy


class StateAnnotation(Gate):
    """state annotation."""

    def __init__(self, theta, phi, lam):
        """Create new annotation gate."""
        super().__init__("annotation", 1, [theta, phi, lam])

    def _define(self):
        """
        gate annotation qubita
        """
        definition = []
        self.definition = definition

    def inverse(self):
        """Invert this gate."""
        raise NotImplemented('TODO: self-inverse?')

    def control(self, num_ctrl_qubits=1, label=None, ctrl_state=None):
        """Controlled version of this gate.

        Args:
            num_ctrl_qubits (int): number of control qubits.
            label (str or None): An optional label for the gate [Default: None]
            ctrl_state (int or str or None): control state expressed as integer,
                string (e.g. '110'), or None. If None, use all 1s.

        Returns:
            ControlledGate: controlled version of this gate.
        """
        raise NotImplemented('TODO')

    def to_matrix(self):
        """Return a Numpy.array for the SwapL gate."""
        raise NotImplemented('TODO')


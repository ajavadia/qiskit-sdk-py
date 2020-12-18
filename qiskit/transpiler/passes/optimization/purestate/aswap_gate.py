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
Asymmetric 2-CNOT-SWAP Gate (ASWAP).

ASWAP:
           |0> --X--       --0--   --X-.--
                 |     =     |   =   | |
         |psi> --X--       --X--   --.-X--
"""
from qiskit.circuit import ControlledGate
from qiskit.circuit import Gate
from qiskit.circuit import QuantumRegister, QuantumCircuit
import numpy


class ASwapGate(Gate):
    """Asymmetric 2-CNOT-SWAP."""

    def __init__(self):
        """Create new ASWAP gate."""
        super().__init__("aswap", 2, [])

    def _define(self):
        """
        gate aswap a,b { cx b,a; cx a,b; }
        """
        q = QuantumRegister(2, 'q')
        definition = QuantumCircuit(q, name=self.name)
        definition.cx(q[1], q[0])
        definition.cx(q[0], q[1])

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
        return numpy.array([[1, 0, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1],
                            [0, 1, 0, 0]], dtype=complex)


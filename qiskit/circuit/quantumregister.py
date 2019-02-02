# -*- coding: utf-8 -*-

# Copyright 2017, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""
Quantum register reference object.
"""
import itertools

from .qubit import Qubit
from .register import Register
from qiskit.exceptions import QiskitError


class QuantumRegister(Register):
    """Implement a quantum register."""

    # Counter for the number of instances in this class.
    instances_counter = itertools.count()

    # Prefix to use for auto naming.
    prefix = 'q'

    def __init__(self, qubits, name=None):
        """Create a new generic register.

        Args:
            qubits (list[Qubit]): list of qubits to group under this register
            name: register string name
        """
        if not all(isinstance(qubit, Qubit) for qubit in qubits):
            raise QiskitError("QuantumRegister can only group Qubits.")

        super().__init__(qubits, name)

    def qasm(self):
        """Return OPENQASM string for this register."""
        return "qreg %s[%d];" % (self.name, self.size)

# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=missing-function-docstring

"""Tests basic functionality of the sequence function"""

from qiskit import QuantumCircuit
from qiskit.compiler import sequence, transpile, schedule
from qiskit.pulse.transforms import pad
from qiskit.test.mock import FakeParis

from qiskit.test import QiskitTestCase


class TestSequence(QiskitTestCase):
    """Test sequence function."""

    def setUp(self):
        self.backend = FakeParis()

    def test_sequence_empty(self):
        self.assertEqual(sequence([], self.backend), [])

    def test_transpile_and_sequence_agree_with_schedule(self):
        qc = QuantumCircuit(2, name="bell")
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()
        sc = transpile(qc, self.backend, scheduling_method='alap')
        actual = sequence(sc, self.backend)
        expected = schedule(qc.decompose(), self.backend)
        self.assertEqual(actual, pad(expected))

    def test_transpile_and_sequence_agree_with_schedule_for_circuits_without_measures(self):
        qc = QuantumCircuit(2, name="bell_without_measurement")
        qc.h(0)
        qc.cx(0, 1)
        sc = transpile(qc, self.backend, scheduling_method='alap')
        actual = sequence(sc, self.backend)
        expected = schedule(qc.decompose(), self.backend)
        self.assertEqual(actual, pad(expected))

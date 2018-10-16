# -*- coding: utf-8 -*-

# Copyright 2017, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# pylint: disable=invalid-name

"""Contains a (slow) python simulator.

It simulates a quantum circuit (an experiment) that has been compiled to run on the
simulator. It is exponential in the number of qubits.

We advise using the c++ simulator or online simulator for larger size systems.

The simulator is run using

.. code-block:: python

    QasmSimulatorPy().run(qobj)

Where the input is a Qobj object and the output is a AerJob object, which can
later be queried for the Result object. The result will contain a 'memory' data
field, which is a result of measurements for each shot.

"""
import random
import uuid
import time
import logging

import numpy as np

from qiskit.qobj import Result as QobjResult
from qiskit.qobj import ExperimentResult as QobjExperimentResult
from qiskit.result import Result
from qiskit.result._utils import copy_qasm_from_qobj_into_result
from qiskit.backends import BaseBackend
from qiskit.backends.aer.aerjob import AerJob
from ._simulatorerror import SimulatorError
from ._simulatortools import single_gate_matrix, index1, index2

logger = logging.getLogger(__name__)


class QasmSimulatorPy(BaseBackend):
    """Python implementation of a qasm simulator."""

    DEFAULT_CONFIGURATION = {
        'backend_name': 'qasm_simulator_py',
        'backend_version': '2.0',
        'n_qubits': -1,
        'url': 'https://github.com/QISKit/qiskit-terra',
        'simulator': True,
        'local': True,
        'conditional': True,
        'description': 'A python simulator for qasm experiments',
        'coupling_map': 'all-to-all',
        'basis_gates': 'u1,u2,u3,cx,id,snapshot'
    }

    def __init__(self, configuration=None, provider=None):
        super().__init__(configuration=configuration or self.DEFAULT_CONFIGURATION.copy(),
                         provider=provider)

        self._local_random = random.Random()

        # Define attributes in __init__.
        self._classical_state = 0
        self._statevector = 0
        self._snapshots = {}
        self._number_of_cbits = 0
        self._number_of_qubits = 0
        self._shots = 0
        self._qobj_config = None

    def _add_qasm_single(self, gate, qubit):
        """Apply an arbitary 1-qubit operator to a qubit.

        Gate is the single qubit applied.
        qubit is the qubit the gate is applied to.
        """
        psi = self._statevector
        bit = 1 << qubit
        for k1 in range(0, 1 << self._number_of_qubits, 1 << (qubit+1)):
            for k2 in range(0, 1 << qubit, 1):
                k = k1 | k2
                cache0 = psi[k]
                cache1 = psi[k | bit]
                psi[k] = gate[0, 0] * cache0 + gate[0, 1] * cache1
                psi[k | bit] = gate[1, 0] * cache0 + gate[1, 1] * cache1

    def _add_qasm_cx(self, q0, q1):
        """Optimized ideal CX on two qubits.

        q0 is the first qubit (control) counts from 0.
        q1 is the second qubit (target).
        """
        psi = self._statevector
        for k in range(0, 1 << (self._number_of_qubits - 2)):
            # first bit is control, second is target
            ind1 = index2(1, q0, 0, q1, k)
            # swap target if control is 1
            ind3 = index2(1, q0, 1, q1, k)
            cache0 = psi[ind1]
            cache1 = psi[ind3]
            psi[ind3] = cache0
            psi[ind1] = cache1

    def _add_qasm_decision(self, qubit):
        """Apply the decision of measurement/reset qubit gate.

        qubit is the qubit that is measured/reset
        """
        probability_zero = 0
        random_number = self._local_random.random()
        for ii in range(1 << self._number_of_qubits):
            if ii & (1 << qubit) == 0:
                probability_zero += np.abs(self._statevector[ii])**2
        if random_number <= probability_zero:
            outcome = '0'
            norm = np.sqrt(probability_zero)
        else:
            outcome = '1'
            norm = np.sqrt(1-probability_zero)
        return (outcome, norm)

    def _add_qasm_measure(self, qubit, cbit):
        """Apply the measurement qubit gate.

        qubit is the qubit measured.
        cbit is the classical bit the measurement is assigned to.
        """
        outcome, norm = self._add_qasm_decision(qubit)
        for ii in range(1 << self._number_of_qubits):
            # update quantum state
            if (ii >> qubit) & 1 == int(outcome):
                self._statevector[ii] = self._statevector[ii]/norm
            else:
                self._statevector[ii] = 0
        # update classical state
        bit = 1 << cbit
        self._classical_state = (self._classical_state & (~bit)) | ((int(outcome)) << cbit)

    def _add_qasm_reset(self, qubit):
        """Apply the reset to the qubit.

        This is done by doing a measurement and if 0 do nothing and
        if 1 flip the qubit.

        qubit is the qubit that is reset.
        """
        # TODO: slow, refactor later
        outcome, norm = self._add_qasm_decision(qubit)
        temp = np.copy(self._statevector)
        self._statevector.fill(0.0)
        # measurement
        for ii in range(1 << self._number_of_qubits):
            if (ii >> qubit) & 1 == int(outcome):
                temp[ii] = temp[ii]/norm
            else:
                temp[ii] = 0
        # reset
        if outcome == '1':
            for ii in range(1 << self._number_of_qubits):
                iip = (~ (1 << qubit)) & ii  # bit number qubit set to zero
                self._statevector[iip] += temp[ii]
        else:
            self._statevector = temp

    def _add_qasm_snapshot(self, slot):
        """Snapshot instruction to record simulator's internal representation
        of quantum statevector.

        Args:
            slot (string): a label to identify the recorded snapshot
        """
        self._snapshots.setdefault(str(int(slot)),
                                   {}).setdefault("statevector",
                                                  []).append(np.copy(self._statevector))

    def run(self, qobj):
        """Run qobj asynchronously.

        Args:
            qobj (Qobj): payload of the experiments

        Returns:
            AerJob: derived from BaseJob
        """
        job_id = str(uuid.uuid4())
        aer_job = AerJob(self, job_id, self._run_job, qobj)
        aer_job.submit()
        return aer_job

    def _run_job(self, job_id, qobj):
        """Run experiments in qobj"""
        self._validate(qobj)
        result_list = []
        self._shots = qobj.config.shots
        self._qobj_config = qobj.config

        start = time.time()

        for experiment in qobj.experiments:
            experiment_result = self.run_experiment(experiment)
            experiment_result['header'] = experiment.header.as_dict()
            result_list.append(QobjExperimentResult(**experiment_result))

        end = time.time()

        result = {'backend_name': self._configuration['backend_name'],
                  'backend_version': self._configuration['backend_version'],
                  'qobj_id': qobj.qobj_id,
                  'job_id': job_id,
                  'results': result_list,
                  'status': 'COMPLETED',
                  'success': True,
                  'time_taken': (end - start)}
        
        copy_qasm_from_qobj_into_result(qobj, result)

        experiment_names = [experiment.header.name for experiment in qobj.experiments]
        return Result(QobjResult(**result), experiment_names)

    def run_experiment(self, experiment):
        """Run an experiment (circuit) and return a single experiment result.

        Args:
            experiment (QobjExperiment): experiment from qobj experiments list

        Returns:
            dict: A result dictionary which looks something like::

                {
                "name": name of this experiment (obtained from qobj.experiment header)
                "seed": random seed used for simulation
                "shots": number of shots used in the simulation
                "data":
                    {
                    "memory": ['0x9', '0xF', '0x1D', ..., '0x9']
                    "snapshots":
                            {
                            '1': [0.7, 0, 0, 0.7],
                            '2': [0.5, 0.5, 0.5, 0.5]
                            }
                    },
                "status": status string for the simulation
                "success": boolean
                "time taken": simulation time of this single experiment
                }

        Raises:
            SimulatorError: if an error occurred.
        """
        self._number_of_qubits = experiment.config.n_qubits
        self._number_of_cbits = experiment.config.memory_slots
        self._statevector = 0
        self._classical_state = 0
        self._snapshots = {}

        # Get the seed looking in experiment, qobj, and then random.
        seed = getattr(experiment.config, 'seed',
                       getattr(self._qobj_config, 'seed',
                               random.getrandbits(32)))
        self._local_random.seed(seed)
        outcomes = []

        start = time.time()
        for _ in range(self._shots):
            self._statevector = np.zeros(1 << self._number_of_qubits,
                                         dtype=complex)
            self._statevector[0] = 1
            self._classical_state = 0
            for operation in experiment.instructions:
                if getattr(operation, 'conditional', None):
                    mask = int(operation.conditional.mask, 16)
                    if mask > 0:
                        value = self._classical_state & mask
                        while (mask & 0x1) == 0:
                            mask >>= 1
                            value >>= 1
                        if value != int(operation.conditional.val, 16):
                            continue
                # Check if single  gate
                if operation.name in ('U', 'u1', 'u2', 'u3'):
                    params = getattr(operation, 'params', None)
                    qubit = operation.qubits[0]
                    gate = single_gate_matrix(operation.name, params)
                    self._add_qasm_single(gate, qubit)
                # Check if CX gate
                elif operation.name in ('id', 'u0'):
                    pass
                elif operation.name in ('CX', 'cx'):
                    qubit0 = operation.qubits[0]
                    qubit1 = operation.qubits[1]
                    self._add_qasm_cx(qubit0, qubit1)
                # Check if measure
                elif operation.name == 'measure':
                    qubit = operation.qubits[0]
                    cbit = operation.memory[0]
                    self._add_qasm_measure(qubit, cbit)
                # Check if reset
                elif operation.name == 'reset':
                    qubit = operation.qubits[0]
                    self._add_qasm_reset(qubit)
                # Check if barrier
                elif operation.name == 'barrier':
                    pass
                # Check if snapshot command
                elif operation.name == 'snapshot':
                    params = operation.params
                    self._add_qasm_snapshot(params[0])
                else:
                    backend = self._configuration['backend_name']
                    err_msg = '{0} encountered unrecognized operation "{1}"'
                    raise SimulatorError(err_msg.format(backend,
                                                        operation.name))
            # Turn classical_state (int) into bit string and pad zero for unused cbits
            outcome = bin(self._classical_state)[2:]

            # Return a compact hexadecimal
            outcomes.append(hex(int(outcome, 2)))

        data = {
            'memory': outcomes,
            'snapshots': self._snapshots
        }
        end = time.time()
        return {'seed': seed,
                'shots': self._shots,
                'data': data,
                'status': 'DONE',
                'success': True,
                'time_taken': (end-start)}

    def _validate(self, qobj):
        for experiment in qobj.experiments:
            if 'measure' not in [op.name for
                                 op in experiment.instructions]:
                logger.warning("no measurements in circuit '%s', "
                               "classical register will remain all zeros.",
                               experiment.header.name)

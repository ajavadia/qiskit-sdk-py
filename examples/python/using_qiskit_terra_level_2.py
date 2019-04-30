# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Example showing how to use Qiskit at level 2 (advanced).

This example shows how an advanced user interacts with Terra.
It builds some circuits and transpiles them with the pass_manager.
"""

import pprint, time

# Import the Qiskit modules
from qiskit import IBMQ, BasicAer
from qiskit import QiskitError
from qiskit.circuit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.compiler import assemble
from qiskit.transpiler import PassManager
from qiskit.providers.ibmq import least_busy
from qiskit.tools.monitor import job_monitor

from qiskit.transpiler.passes import BasicSwap
from qiskit.transpiler.coupling import CouplingMap
from qiskit.transpiler.passes.unroller import Unroller


try:
    IBMQ.load_accounts()
except:
    print("""WARNING: There's no connection with the API for remote backends.
             Have you initialized a file with your personal token?
             For now, there's only access to local simulator backends...""")

try:
    # Create a Quantum and Classical Register and give them names.
    qubit_reg = QuantumRegister(2, name='q')
    clbit_reg = ClassicalRegister(2, name='c')

    # Making first circuit: bell state
    qc1 = QuantumCircuit(qubit_reg, clbit_reg, name="bell")
    qc1.h(qubit_reg[0])
    qc1.cx(qubit_reg[0], qubit_reg[1])
    qc1.measure(qubit_reg, clbit_reg)

    # Making another circuit: superpositions
    qc2 = QuantumCircuit(qubit_reg, clbit_reg, name="superposition")
    qc2.h(qubit_reg)
    qc2.measure(qubit_reg, clbit_reg)

    # Setting up the backend
    print("(Aer Backends)")
    for backend in BasicAer.backends():
        print(backend.status())
    qasm_simulator = BasicAer.get_backend('qasm_simulator')


    # Compile and run the circuit on a real device backend
    # See a list of available remote backends
    print("\n(IBMQ Backends)")
    for backend in IBMQ.backends():
        print(backend.status())

    try:
        # select least busy available device and execute.
        least_busy_device = least_busy(IBMQ.backends(simulator=False))
    except:
        print("All devices are currently unavailable.")

    print("Running on current least busy device: ", least_busy_device)


    # making a pass manager to compile the circuits
    pm = PassManager()
    pm.append(Unroller(['u1', 'u2', 'u3', 'id', 'cx']))
    coupling_map = CouplingMap(least_busy_device.configuration().coupling_map)
    pm.appaend(BasicSwap(coupling_map))
    qc1_new = pm.run(qc1)
    qc2_new = pm.run(qc2)

    print("Bell circuit before passes:")
    print(qc1.draw())
    print("Bell circuit after passes:")
    print(qc1_new.draw())
    print("Superposition circuit before passes:")
    print(qc2.draw())
    print("Superposition circuit after passes:")
    print(qc2_new.draw())

    # Assemble the two circuits into a runnable qobj
    qobj = assemble([qc1_new, qc2_new], shots=1000)

    # Running qobj on the simulator
    sim_job = qasm_simulator.run(qobj)

    # Getting the result
    sim_result=sim_job.result()

    # Show the results
    print(sim_result.get_counts(qc1))
    print(sim_result.get_counts(qc2))

    # Running the job.
    exp_job = least_busy_device.run(qobj)

    job_monitor(exp_job)
    exp_result = exp_job.result()

    # Show the results
    print(exp_result.get_counts(qc1))
    print(exp_result.get_counts(qc2))

except QiskitError as ex:
    print('There was an error in the circuit!. Error = {}'.format(ex))

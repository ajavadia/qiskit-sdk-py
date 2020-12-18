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

"""Optimize CXs and Swaps when on constants."""

from qiskit.transpiler.basepasses import TransformationPass
from qiskit.extensions.standard import SwapGate, XGate, YGate, ZGate, SGate, TGate, SdgGate, \
    TdgGate, HGate

from qiskit.circuit import QuantumRegister, ControlledGate, Reset
from qiskit.dagcircuit import DAGCircuit
from .aswap_gate import ASwapGate


class ConstantsStateOptimization(TransformationPass):
    # These gate have no effect and are ignored
    nothing_gates = (SGate, TGate, SdgGate, TdgGate)

    swap_rules = {('0', '-'): [(XGate, ['top']),
                               (HGate, ['top']),
                               (HGate, ['bot']),
                               (XGate, ['bot'])],
                  ('1', '+'): ('0', '-'),
                  (None, '-'): [(ZGate, ['top']),
                                (ASwapGate, ['top', 'bot'])],
                  ('-', None): [(ZGate, ['bot']),
                                (ASwapGate, ['bot', 'top'])],
                  ('1', None): [(XGate, ['bot']),
                                (ASwapGate, ['top', 'bot'])],
                  (None, '1'): [(XGate, ['top']),
                                (ASwapGate, ['bot', 'top'])],
                  ('+', '-'): [(ZGate, ['top']),
                               (ZGate, ['bot'])],
                  ('-', '+'): ('+', '-'),
                  ('+', None): (None, '0'),
                  (None, '0'): [(ASwapGate, ['bot', 'top'])],
                  ('0', None): (None, '+'),
                  (None, '+'): [(ASwapGate, ['top', 'bot'])],
                  ('0', '1'): ('1', '0'),
                  ('1', '0'): [(XGate, ['top']),
                               (XGate, ['bot'])],
                  ('0', '+'): [(HGate, ['top']),
                               (HGate, ['bot'])],
                  ('+', '0'): ('0', '+'),
                  ('1', '-'): ('0', '+'),
                  ('-', '1'): ('0', '+'),
                  ('-', '0'): ('+', '1'),
                  ('+', '1'): [(HGate, ['top']),
                               (XGate, ['top']),
                               (XGate, ['bot']),
                               (HGate, ['bot'])]
                  }

    def __init__(self):
        self.wire_state = None
        super().__init__()

    def run(self, dag):
        """Run the ConstantsStateOptimization optimization pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to optimize.

        Returns:
            DAGCircuit: Optimized DAG.
        """
        self.wire_state = WireStatus(dag.qubits)

        for node in dag.topological_op_nodes():
            if isinstance(node.op, ControlledGate):
                controlled_qubits = node.qargs[:node.op.num_ctrl_qubits]
                if type(node.op.base_gate) == XGate and self.wire_state[node.qargs[-1]] == '+':
                    # Target on |+> can remove CX (it does not matter who many controls)
                    dag.remove_op_node(node)
                    continue
                bin_ctrl_state = "{0:b}".format(node.op.ctrl_state).rjust(
                    node.op.num_ctrl_qubits, '0')[::-1]
                new_state = ''
                new_ctrl_qubits = []

                for qubit, state in zip(controlled_qubits, bin_ctrl_state):
                    if self.wire_state[qubit] in [None, '+', '-']:
                        new_state += state
                        new_ctrl_qubits.append(qubit)
                    elif self.wire_state[qubit] != state:
                        # The conditions cannot be fulfilled, so the full operation can be removed
                        dag.remove_op_node(node)
                        break
                else:
                    if self.wire_state[node.qargs[-1]] == '-':
                        if not new_ctrl_qubits and self.wire_state[node.qargs[0]] in ['0', '1']:
                            dag.remove_op_node(node)
                            break
                        else:
                            new_dag = ConstantsStateOptimization.z_dag(node, new_state, new_ctrl_qubits)
                    else:
                        if bin_ctrl_state == new_state and new_ctrl_qubits == controlled_qubits:
                            # The node has no modification
                            self.constant_analysis([node])
                            continue
                        new_dag = ConstantsStateOptimization.toffoli_dag(node, new_state, new_ctrl_qubits)
                    self.constant_analysis(new_dag.topological_op_nodes(), wires=node.qargs)
                    dag.substitute_node_with_dag(node, new_dag)
            elif isinstance(node.op, SwapGate):
                if self.wire_state[node.qargs[0]] == self.wire_state[node.qargs[1]] == None:
                    # This Swap should stay here
                    continue
                if self.wire_state[node.qargs[0]] == self.wire_state[node.qargs[1]]:
                    # This Swap can be removed
                    dag.remove_op_node(node)
                    continue
                swap_dag = self.swap_dag(node.qargs[0], node.qargs[1])
                dag.substitute_node_with_dag(node, swap_dag)
                self.wire_state.swap(node.qargs[0], node.qargs[1])
            else:
                # The node has no modification
                self.constant_analysis([node])
        return dag

    def constant_analysis(self, nodes, wires=None):
        """ Nodes in topological order"""
        for node in nodes:
            if wires:
                qargs = []
                for qarg in node.qargs:
                    qargs.append(wires[qarg.index])
            else:
                qargs = node.qargs
            if isinstance(node.op, self.wire_state.available_rules):
                self.wire_state[qargs[0]] = type(node.op)
            elif isinstance(node.op, Reset):
                self.wire_state[qargs[0]] = '0'
            elif isinstance(node.op, self.nothing_gates):
                continue
            else:
                # Any other state is not constant
                for qarg in qargs:
                    self.wire_state[qarg] = None

    @staticmethod
    def toffoli_dag(node, state, ctrl_qubits):
        new_dag = DAGCircuit()
        reg = QuantumRegister(len(node.qargs))
        new_dag.add_qreg(reg)

        new_qarg = []
        for qarg in node.qargs:
            new_qarg.append(reg[node.qargs.index(qarg)])

        new_ctrl_qubits = []
        for qarg in ctrl_qubits:
            new_ctrl_qubits.append(reg[node.qargs.index(qarg)])

        if len(state):
            op = node.op.base_gate.control(len(state), ctrl_state=state)
        else:
            op = node.op.base_gate
        new_dag.apply_operation_back(op, new_ctrl_qubits + new_qarg[node.op.num_ctrl_qubits:])
        return new_dag

    @staticmethod
    def z_dag(node, state, ctrl_qubits):
        new_dag = DAGCircuit()
        reg = QuantumRegister(len(node.qargs))
        new_dag.add_qreg(reg)

        new_qarg = []
        for qarg in node.qargs:
            new_qarg.append(reg[node.qargs.index(qarg)])

        new_ctrl_qubits = []
        for qarg in ctrl_qubits:
            new_ctrl_qubits.append(reg[node.qargs.index(qarg)])

        if len(state) == 1:
            op = ZGate()
            new_dag.apply_operation_back(op, new_ctrl_qubits)
        else:
            # With multiple places to put the Z gate in, choose the one with
            # the closed control, if possible.
            try:
                z_index = state.index('1')
            except ValueError:
                # It was not possible  so the open control is replaced by x-z-x
                raise Exception('TODO')
            else:
                # there is a closed controlled where to put the gate.
                state = state[0: z_index:] + state[z_index + 1::]
                op = ZGate().control(len(state), ctrl_state=state)
                z_qubit = new_ctrl_qubits[z_index]
                del new_ctrl_qubits[z_index]
                new_dag.apply_operation_back(op, new_ctrl_qubits + [z_qubit])
        return new_dag

    def swap_dag(self, top, bot):
        new_dag = DAGCircuit()
        states = (self.wire_state[top], self.wire_state[bot])
        reg = QuantumRegister(2)
        new_dag.add_qreg(reg)

        rules = ConstantsStateOptimization.get_swap_rules(states)
        ConstantsStateOptimization.extend_dag(rules, new_dag, top=reg[0], bot=reg[1])
        return new_dag

    @staticmethod
    def get_swap_rules(states):
        rules = ConstantsStateOptimization.swap_rules.get(states)
        if isinstance(rules, tuple):
            rules = ConstantsStateOptimization.swap_rules.get(rules)
        return rules

    @staticmethod
    def extend_dag(rules, dag, **kwargs):
        for rule in rules:
            args = [kwargs[var] for var in rule[1]]
            dag.apply_operation_back(rule[0](), args)


class WireStatus():
    # wire_state is a maps qubit -> {"0","1","+","-", None}
    # meaning that qubit is in constant |0>, |1>, |+>, or |->.
    # Otherwise, None.

    rules = {HGate: {'0': '+',
                     '1': '-',
                     '+': '0',
                     '-': '1'},
             ZGate: {'0': '0',
                     '1': '1',
                     '+': '-',
                     '-': '+'},
             XGate: {'0': '1',
                     '1': '0',
                     '+': '+',
                     '-': '-'},
             YGate: {'0': '1',
                     '1': '0',
                     '+': '-',
                     '-': '+'}
             }

    def __init__(self, qubits):
        self._dict = {qubit: '0' for qubit in qubits}

    def __setitem__(self, key, item):
        rule = self.rules.get(item)
        if rule:
            if self._dict[key] is not None:
                self._dict[key] = rule[self._dict[key]]
        else:
            self._dict[key] = item

    def __getitem__(self, key):
        return self._dict[key]

    def __repr__(self):
        return repr(self._dict)

    def swap(self, qubit1, qubit2):
        self._dict[qubit1], self._dict[qubit2] = self._dict[qubit2], self._dict[qubit1]

    @property
    def available_rules(self):
        return tuple(self.rules.keys())

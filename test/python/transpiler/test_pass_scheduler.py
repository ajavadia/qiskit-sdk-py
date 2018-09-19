# -*- coding: utf-8 -*-

# Copyright 2018, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# pylint: disable=invalid-name

"""Tranpiler testing"""

import unittest.mock

from qiskit import QuantumRegister, QuantumCircuit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import PassManager, transpile, TranspilerAccessError, TranspilerError, \
    ControlFlowPlugin
from qiskit.transpiler._passmanager import PluginDoWhile
from ._dummy_passes import DummyTP, PassA_TP_NR_NP, PassB_TP_RA_PA, PassC_TP_RA_PA, \
    PassD_TP_NR_NP, PassE_AP_NR_NP, PassF_reduce_dag_property, PassG_calculates_dag_property, \
    PassH_Bad_TP, PassI_Bad_AP, PassJ_Bad_NoReturn
from ..common import QiskitTestCase

logger = "LocalLogger"


class SchedulerTestCase(QiskitTestCase):
    """ Asserts for the scheduler. """

    def assertScheduler(self, dag, passmanager, expected):
        """
        Runs transpiler(dag, passmanager) and checks if the passes run as expected.
        Args:
            dag (DAGCircuit): DAG circuit to transform via transpilation.
            passmanager (PassManager): pass manager instance for the tranpilation process
            expected (list): List of things the passes are logging
        """
        with self.assertLogs(logger, level='INFO') as cm:
            transpile(dag, pass_manager=passmanager)
        self.assertEqual([record.message for record in cm.records], expected)

    def assertSchedulerRaises(self, dag, passmanager, expected, exception_type):
        """
        Runs transpiler(dag, passmanager) and checks if the passes run as expected until
        expcetion_type is raised.
        Args:
            dag (DAGCircuit): DAG circuit to transform via transpilation
            passmanager (PassManager): pass manager instance for the tranpilation process
            expected (list): List of things the passes are logging
            exception_type (Exception): Exception that is expected to be raised.
        """
        with self.assertLogs(logger, level='INFO') as cm:
            self.assertRaises(exception_type, transpile, dag, pass_manager=passmanager)
        self.assertEqual([record.message for record in cm.records], expected)


class TestUseCases(SchedulerTestCase):
    """ The pass manager schedules passes in, sometimes, tricky ways. These tests combine passes in
     many ways, and checks that passes are ran in the right order. """

    def setUp(self):
        self.dag = DAGCircuit.fromQuantumCircuit(QuantumCircuit(QuantumRegister(1)))
        self.passmanager = PassManager()

    def test_chain(self):
        """ A single chain of passes, with Requests and Preserves."""
        self.passmanager.add_pass(PassC_TP_RA_PA())  # Request: PassA / Preserves: PassA
        self.passmanager.add_pass(PassB_TP_RA_PA())  # Request: PassA / Preserves: PassA
        self.passmanager.add_pass(PassD_TP_NR_NP(argument1=[1, 2]))  # Requires: {} / Preserves: {}
        self.passmanager.add_pass(PassB_TP_RA_PA())
        self.assertScheduler(self.dag, self.passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                          'run transformation pass PassC_TP_RA_PA',
                                                          'run transformation pass PassB_TP_RA_PA',
                                                          'run transformation pass PassD_TP_NR_NP',
                                                          'argument [1, 2]',
                                                          'run transformation pass PassA_TP_NR_NP',
                                                          'run transformation pass PassB_TP_RA_PA'])

    def test_conditional_passes_true(self):
        """ A pass set with a conditional parameter. The callable is True. """
        self.passmanager.add_pass(PassE_AP_NR_NP(True))
        self.passmanager.add_pass(PassA_TP_NR_NP(),
                                  condition=lambda property_set: property_set['property'])
        self.assertScheduler(self.dag, self.passmanager, ['run analysis pass PassE_AP_NR_NP',
                                                          'set property as True',
                                                          'run transformation pass PassA_TP_NR_NP'])

    def test_conditional_passes_false(self):
        """ A pass set with a conditional parameter. The callable is False. """
        self.passmanager.add_pass(PassE_AP_NR_NP(False))
        self.passmanager.add_pass(PassA_TP_NR_NP(),
                                  condition=lambda property_set: property_set['property'])
        self.assertScheduler(self.dag, self.passmanager, ['run analysis pass PassE_AP_NR_NP',
                                                          'set property as False'])

    def test_do_while_until_fixed_point(self):
        """ A pass set with a do_while parameter that checks for a fixed point. """
        self.passmanager.add_pass([
            PassF_reduce_dag_property(),
            PassA_TP_NR_NP(),  # Since preserves nothings,  allows PassF to loop
            PassG_calculates_dag_property()], \
            do_while=lambda property_set: not property_set['fixed_point']['property'])
        self.assertScheduler(self.dag, self.passmanager,
                             ['run transformation pass PassF_reduce_dag_property',
                              'dag property = 6',
                              'run transformation pass PassA_TP_NR_NP',
                              'run analysis pass PassG_calculates_dag_property',
                              'set property as 6 (from dag.property)',
                              'run transformation pass PassF_reduce_dag_property',
                              'dag property = 5',
                              'run transformation pass PassA_TP_NR_NP',
                              'run analysis pass PassG_calculates_dag_property',
                              'set property as 5 (from dag.property)',
                              'run transformation pass PassF_reduce_dag_property',
                              'dag property = 4',
                              'run transformation pass PassA_TP_NR_NP',
                              'run analysis pass PassG_calculates_dag_property',
                              'set property as 4 (from dag.property)',
                              'run transformation pass PassF_reduce_dag_property',
                              'dag property = 3',
                              'run transformation pass PassA_TP_NR_NP',
                              'run analysis pass PassG_calculates_dag_property',
                              'set property as 3 (from dag.property)',
                              'run transformation pass PassF_reduce_dag_property',
                              'dag property = 2',
                              'run transformation pass PassA_TP_NR_NP',
                              'run analysis pass PassG_calculates_dag_property',
                              'set property as 2 (from dag.property)',
                              'run transformation pass PassF_reduce_dag_property',
                              'dag property = 2',
                              'run transformation pass PassA_TP_NR_NP',
                              'run analysis pass PassG_calculates_dag_property',
                              'set property as 2 (from dag.property)'])

    def test_do_while_until_max_iterationt(self):
        """ A pass set with a do_while parameter that checks that the max_iteration is raised. """
        self.passmanager.add_pass(
            [PassF_reduce_dag_property(),
             PassA_TP_NR_NP(),  # Since preserves nothings,  allows PassF to loop
             PassG_calculates_dag_property()],
            do_while=lambda property_set: not property_set['fixed_point']['property'],
            max_iteration=2)
        self.assertSchedulerRaises(self.dag, self.passmanager,
                                   ['run transformation pass PassF_reduce_dag_property',
                                    'dag property = 6',
                                    'run transformation pass PassA_TP_NR_NP',
                                    'run analysis pass PassG_calculates_dag_property',
                                    'set property as 6 (from dag.property)',
                                    'run transformation pass PassF_reduce_dag_property',
                                    'dag property = 5',
                                    'run transformation pass PassA_TP_NR_NP',
                                    'run analysis pass PassG_calculates_dag_property',
                                    'set property as 5 (from dag.property)'], TranspilerError)

    def test_do_not_repeat_based_on_preservation(self):
        """ When a pass is still a valid pass (because following passes preserved it), it should not
        run again"""
        self.passmanager.add_pass([PassB_TP_RA_PA(), PassA_TP_NR_NP(), PassB_TP_RA_PA()])
        self.assertScheduler(self.dag, self.passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                          'run transformation pass PassB_TP_RA_PA'])

    def test_do_not_repeat_based_on_idempotence(self):
        """ By default, passes are idempotent. Therefore, repetition can be optimized to a single
        execution"""
        self.passmanager.add_pass(PassA_TP_NR_NP())
        self.passmanager.add_pass([PassA_TP_NR_NP(), PassA_TP_NR_NP()])
        self.passmanager.add_pass(PassA_TP_NR_NP())
        self.assertScheduler(self.dag, self.passmanager, ['run transformation pass PassA_TP_NR_NP'])

    def test_fenced_property_set(self):
        """ Transformation passes are not allowed to modified the property set. """
        self.passmanager.add_pass(PassH_Bad_TP())
        self.assertSchedulerRaises(self.dag, self.passmanager,
                                   ['run transformation pass PassH_Bad_TP'],
                                   TranspilerAccessError)

    def test_fenced_dag(self):
        """ Analysis passes are not allowed to modified the DAG. """
        qr = QuantumRegister(2)
        circ = QuantumCircuit(qr)
        # pylint: disable=no-member
        circ.cx(qr[0], qr[1])
        circ.cx(qr[0], qr[1])
        circ.cx(qr[1], qr[0])
        circ.cx(qr[1], qr[0])
        dag = DAGCircuit.fromQuantumCircuit(circ)

        self.passmanager.add_pass(PassI_Bad_AP())
        self.assertSchedulerRaises(dag, self.passmanager,
                                   ['run analysis pass PassI_Bad_AP',
                                    'cx_runs: {(5, 6, 7, 8)}'],
                                   TranspilerAccessError)

    def test_ignore_request_pm(self):
        """ A pass manager that ignores requests does not run the passes decleared in the 'requests'
        field of the passes."""
        passmanager = PassManager(ignore_requires=True)
        passmanager.add_pass(PassC_TP_RA_PA())  # Request: PassA / Preserves: PassA
        passmanager.add_pass(PassB_TP_RA_PA())  # Request: PassA / Preserves: PassA
        passmanager.add_pass(PassD_TP_NR_NP(argument1=[1, 2]))  # Requires: {} / Preserves: {}
        passmanager.add_pass(PassB_TP_RA_PA())
        self.assertScheduler(self.dag, passmanager, ['run transformation pass PassC_TP_RA_PA',
                                                     'run transformation pass PassB_TP_RA_PA',
                                                     'run transformation pass PassD_TP_NR_NP',
                                                     'argument [1, 2]',
                                                     'run transformation pass PassB_TP_RA_PA'])

    def test_ignore_preserves_pm(self):
        """ A pass manager that ignores preserves does not record the passes decleared in the
        'preserves' field of the passes as valid passes."""
        passmanager = PassManager(ignore_preserves=True)
        passmanager.add_pass(PassC_TP_RA_PA())  # Request: PassA / Preserves: PassA
        passmanager.add_pass(PassB_TP_RA_PA())  # Request: PassA / Preserves: PassA
        passmanager.add_pass(PassD_TP_NR_NP(argument1=[1, 2]))  # Requires: {} / Preserves: {}
        passmanager.add_pass(PassB_TP_RA_PA())
        self.assertScheduler(self.dag, passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassC_TP_RA_PA',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassB_TP_RA_PA',
                                                     'run transformation pass PassD_TP_NR_NP',
                                                     'argument [1, 2]',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassB_TP_RA_PA'])

    def test_pass_idempotence_pm(self):
        """ A pass manager that considers every pass as not idempotent, allows the immediate
        repetition of a pass"""
        passmanager = PassManager(idempotence=False)
        passmanager.add_pass(PassA_TP_NR_NP())
        passmanager.add_pass(PassA_TP_NR_NP())  # Normally removed for optimization, not here.
        passmanager.add_pass(PassB_TP_RA_PA())  # Normally requiered is ignored for optimization,
        # not here
        self.assertScheduler(self.dag, passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassB_TP_RA_PA'])

    def test_pass_idempotence_passset(self):
        """ A pass set that is not idempotent. """
        passmanager = PassManager()
        passmanager.add_pass([PassA_TP_NR_NP(), PassB_TP_RA_PA()], idempotence=False)
        self.assertScheduler(self.dag, passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassB_TP_RA_PA'])

    def test_pass_idempotence_single_pass(self):
        """ A single pass that is not idempotent. """
        passmanager = PassManager()
        pass_a = PassA_TP_NR_NP()
        pass_a.set(idempotence=False)  # Set idempotence as False

        passmanager.add_pass(pass_a)
        passmanager.add_pass(pass_a)  # Normally removed for optimization, not here.
        passmanager.add_pass(PassB_TP_RA_PA())  # Normally requiered is ignored for optimization,
        # not here
        passmanager.add_pass(PassA_TP_NR_NP())  # This is not run because is idempotent and it was
        # already ran as PassB requirment.
        self.assertScheduler(self.dag, passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassA_TP_NR_NP',
                                                     'run transformation pass PassB_TP_RA_PA'])

    def test_pass_option_precedence(self):
        """ The precedence of options for a pass is:
         - The pass
         - The pass set
         - The pass manager option
        """
        passmanager = PassManager(idempotence=True, ignore_preserves=False, ignore_requires=True)
        tp_pass = DummyTP()
        tp_pass.set(idempotence=False)
        passmanager.add_pass(tp_pass, idempotence=True, ignore_preserves=True)
        the_pass_in_the_workinglist = next(iter(passmanager.working_list))
        self.assertFalse(the_pass_in_the_workinglist.idempotence)
        self.assertTrue(the_pass_in_the_workinglist.ignore_preserves)
        self.assertTrue(the_pass_in_the_workinglist.ignore_requires)

    def test_pass_no_return_a_dag(self):
        """ Passes instances with same arguments (independently of the order) are the same. """
        self.passmanager.add_pass(PassJ_Bad_NoReturn())
        self.assertSchedulerRaises(self.dag, self.passmanager,
                                   ['run transformation pass PassJ_Bad_NoReturn'], TranspilerError)


class DoXTimesPlugin(ControlFlowPlugin):
    """ A control-flow plugin for running a set of passes an X amount of times."""

    def __init__(self, passes, do_x_times=0, **_):  # pylint: disable=super-init-not-called
        self.do_x_times = do_x_times
        super().__init__(passes)

    def __iter__(self):
        for _ in range(self.do_x_times):
            for pass_ in self.working_list:
                yield pass_


class TestControlFlowPlugin(SchedulerTestCase):
    """ Testing the control flow plugin system. """

    def setUp(self):
        self.passmanager = PassManager()
        self.dag = DAGCircuit.fromQuantumCircuit(QuantumCircuit(QuantumRegister(1)))

    def test_control_flow_plugin(self):
        """ Adds a control flow plugin with a single parameter and runs it. """
        self.passmanager.add_control_flow_plugin('do_x_times', DoXTimesPlugin)
        self.passmanager.add_pass([PassB_TP_RA_PA(), PassC_TP_RA_PA()], do_x_times=3)
        self.assertScheduler(self.dag, self.passmanager, ['run transformation pass PassA_TP_NR_NP',
                                                          'run transformation pass PassB_TP_RA_PA',
                                                          'run transformation pass PassC_TP_RA_PA',
                                                          'run transformation pass PassB_TP_RA_PA',
                                                          'run transformation pass PassC_TP_RA_PA',
                                                          'run transformation pass PassB_TP_RA_PA',
                                                          'run transformation pass PassC_TP_RA_PA'])

    def test_callable_control_flow_plugin(self):
        """ Removes do_while, then adds it back. Checks max_iteration still working. """
        self.passmanager.remove_control_flow_plugin('do_while')
        self.passmanager.add_control_flow_plugin('do_while', PluginDoWhile)
        self.passmanager.add_pass([PassB_TP_RA_PA(), PassC_TP_RA_PA()],
                                  do_while=lambda property_set: True, max_iteration=2)
        self.assertSchedulerRaises(self.dag, self.passmanager,
                                   ['run transformation pass PassA_TP_NR_NP',
                                    'run transformation pass PassB_TP_RA_PA',
                                    'run transformation pass PassC_TP_RA_PA',
                                    'run transformation pass PassB_TP_RA_PA',
                                    'run transformation pass PassC_TP_RA_PA'], TranspilerError)

    def test_remove_unexistent_plugin(self):
        """ Tries to remove a plugin that does not exist. """
        self.assertRaises(KeyError, self.passmanager.remove_control_flow_plugin, "foo")


if __name__ == '__main__':
    unittest.main()

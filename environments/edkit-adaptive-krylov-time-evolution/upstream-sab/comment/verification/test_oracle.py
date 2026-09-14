"""Small offline fault-rejection tests for the ED oracle and SAB pair policy."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

CHECK = Path(__file__).resolve().parents[2] / "tests/checks/operator-dense-reference"

def load_policy(name):
    spec = importlib.util.spec_from_file_location(name, CHECK / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

oracle = load_policy("oracle")
validate = load_policy("validate")


RUBRIC = {
    "policy": "pointwise",
    "comparison": {
        "atol": 1e-10, "rtol": 0.0,
        "scientific": {
            "state_atol": 1e-11, "state_rtol": 0.0,
            "l2_atol": 1e-11, "l2_rtol": 0.0,
            "norm_atol": 1e-11, "norm_rtol": 0.0,
            "energy_atol": 1e-11, "energy_rtol": 0.0,
        },
    },
}


def case(initial=1.0):
    return {"id": "evolve", "mode": "multi", "times": [0.0, 0.31, 0.9],
            "state_real": [initial, 0.0], "state_imag": [0.0, 0.0],
            "hamiltonian": {"kind": "dense", "real": [[0.0, 1.0], [1.0, 0.0]], "imag": [[0.0, 0.0], [0.0, 0.0]]},
            "expected_statuses": {}, "options": {}}


def input_doc(row):
    return {"schema_version": 1, "check": "synthetic", "variant": "nominal", "cases": [row]}


def result_doc(row, scale=1.0):
    # Analytic sigma_x evolution, independent of both numerical eigensolvers.
    times = np.asarray(row["times"]) * scale
    amplitude = row["state_real"][0]
    states = np.column_stack((amplitude * np.cos(times), -1j * amplitude * np.sin(times)))
    return {"schema_version": 1, "check": "synthetic", "cases": [
        {"id": row["id"], "times": times.tolist(), "states_real": states.real.tolist(),
         "states_imag": states.imag.tolist(), "statuses": {}}]}


def from_states(row, states, times=None):
    if times is None:
        times = row["times"]
    return {"schema_version": 1, "check": "synthetic", "cases": [
        {"id": row["id"], "times": list(times), "states_real": states.real.tolist(),
         "states_imag": states.imag.tolist(), "statuses": {}}]}


class ScientificOracleTests(unittest.TestCase):
    def test_independent_analytic_sigma_x(self):
        row = case()
        report = oracle.evaluate(input_doc(row), result_doc(row), RUBRIC)
        self.assertTrue(report["passed"], report)

    def test_wrong_sign_rejected_even_with_norm_and_energy_conserved(self):
        row = case()
        result = result_doc(row)
        result["cases"][0]["states_imag"] = (-np.asarray(result["cases"][0]["states_imag"])).tolist()
        report = oracle.evaluate(input_doc(row), result, RUBRIC)
        metrics = report["cases"]["evolve"]["metrics"]
        self.assertFalse(report["passed"])
        self.assertTrue(metrics["norm"]["passed"])
        self.assertTrue(metrics["energy"]["passed"])
        self.assertFalse(metrics["state"]["passed"])

    def test_global_phase_is_not_aligned_away(self):
        row = case()
        result = result_doc(row)
        states = validate.states(result["cases"][0]) * np.exp(0.1j)
        self.assertFalse(oracle.evaluate(input_doc(row), from_states(row, states), RUBRIC)["passed"])

    def test_nonunit_input_preserved(self):
        row = case(2.3)
        correct = result_doc(row)
        self.assertTrue(oracle.evaluate(input_doc(row), correct, RUBRIC)["passed"])
        normalized = validate.states(correct["cases"][0]) / 2.3
        self.assertFalse(oracle.evaluate(input_doc(row), from_states(row, normalized), RUBRIC)["passed"])

    def test_explicit_normalize_output(self):
        row = case(2.3)
        row["options"]["normalize_output"] = True
        normalized = validate.states(result_doc(row)["cases"][0]) / 2.3
        self.assertTrue(oracle.evaluate(input_doc(row), from_states(row, normalized), RUBRIC)["passed"])

    def test_nan_rejected(self):
        row = case()
        result = result_doc(row)
        result["cases"][0]["states_real"][0][0] = float("nan")
        self.assertFalse(oracle.evaluate(input_doc(row), result, RUBRIC)["passed"])

    def test_missing_column_rejected(self):
        row = case()
        result = result_doc(row)
        result["cases"][0]["states_real"] = [[value[0]] for value in result["cases"][0]["states_real"]]
        result["cases"][0]["states_imag"] = [[value[0]] for value in result["cases"][0]["states_imag"]]
        self.assertFalse(oracle.evaluate(input_doc(row), result, RUBRIC)["passed"])

    def test_zero_norm_fails_cleanly(self):
        row = case()
        zero = np.zeros((3, 2), dtype=complex)
        report = oracle.evaluate(input_doc(row), from_states(row, zero), RUBRIC)
        self.assertFalse(report["passed"])
        self.assertIn("nonzero state norm", report["cases"]["evolve"]["failures"][0])

    def test_case_override_is_rubric_owned(self):
        row = case()
        result = result_doc(row)
        result["cases"][0]["states_real"][1][0] += 2e-9
        row["upstream_bounds"] = {"state_l2": 1.0}
        self.assertFalse(oracle.evaluate(input_doc(row), result, RUBRIC)["passed"])
        rubric = copy.deepcopy(RUBRIC)
        rubric["comparison"]["scientific"]["case_overrides"] = {
            "evolve": {"state_atol": 1e-8, "l2_atol": 1e-8, "norm_atol": 1e-8, "energy_atol": 1e-8}}
        self.assertTrue(oracle.evaluate(input_doc(row), result, rubric)["passed"])

    def test_nonhermitian_fixture_rejected(self):
        row = case()
        row["hamiltonian"]["real"][1][0] = 2.0
        self.assertFalse(oracle.evaluate(input_doc(row), result_doc(row), RUBRIC)["passed"])

    def test_variant_gets_its_own_reference(self):
        row = case(np.nextafter(np.nextafter(1.0, np.inf), np.inf))
        inputs = input_doc(row)
        inputs["variant"] = "variant"
        self.assertTrue(oracle.evaluate(inputs, result_doc(row), RUBRIC)["passed"])
        self.assertNotEqual(oracle.expected_states(row)[0][0, 0].real, oracle.expected_states(case())[0][0, 0].real)

    def test_diagonal_oracle_analytic_control(self):
        row = case()
        row["hamiltonian"] = {"kind": "diagonal", "values": [-2.0, 5.0], "shift": 0.7}
        row["state_real"] = [0.3, 1.2]
        row["state_imag"] = [0.8, -0.1]
        psi = np.array([0.3 + 0.8j, 1.2 - 0.1j])
        states = np.exp(-1j * np.outer(row["times"], [-1.3, 5.7])) * psi
        self.assertTrue(oracle.evaluate(input_doc(row), from_states(row, states), RUBRIC)["passed"])

    def test_trusted_shortening_and_forged_times(self):
        row = case()
        short = result_doc(row, scale=0.5)
        with patch.dict(os.environ, {"SAB_TIME_SCALE": "0.5"}):
            self.assertTrue(oracle.evaluate(input_doc(row), short, RUBRIC)["passed"])
        self.assertFalse(oracle.evaluate(input_doc(row), short, RUBRIC)["passed"])
        forged = result_doc(row)
        forged["cases"][0]["times"][1] += 0.01
        self.assertFalse(oracle.evaluate(input_doc(row), forged, RUBRIC)["passed"])

    def test_density_keeps_input_norm(self):
        row = case(2.0)
        row.update(observable="density", dimension=2, normalize_density=False)
        psi = validate.states(result_doc(row)["cases"][0])
        rho = np.array([np.outer(state, state.conj()).reshape(-1, order="F") for state in psi])
        report = oracle.evaluate(input_doc(row), from_states(row, rho), RUBRIC)
        self.assertTrue(report["passed"], report)
        self.assertFalse(oracle.evaluate(input_doc(row), from_states(row, rho / 4.0), RUBRIC)["passed"])

    def test_declared_magnetization_is_gated(self):
        row = case()
        row.update(state_real=[0.0, 1.0, 0.0, 0.0], state_imag=[0.0] * 4, measure=["magnetization_site1"])
        row["hamiltonian"] = {"kind": "xxz", "L": 2, "delta": 0.7, "flip": 0.5, "periodic": False}
        expected, _, times = oracle.expected_states(row)
        result = from_states(row, expected, times)
        values = np.sum(np.abs(expected) ** 2 * [0.5, 0.5, -0.5, -0.5], axis=1)
        result["cases"][0]["observables"] = {"magnetization_site1": values.tolist()}
        rubric = copy.deepcopy(RUBRIC)
        rubric["comparison"]["scientific"].update(observable_atol=1e-11, observable_rtol=0.0)
        self.assertTrue(oracle.evaluate(input_doc(row), result, rubric)["passed"])
        result["cases"][0]["observables"]["magnetization_site1"][1] += 1e-3
        self.assertFalse(oracle.evaluate(input_doc(row), result, rubric)["passed"])

    def test_density_cross_check(self):
        state_row = case()
        density_row = copy.deepcopy(state_row)
        density_row.update(id="density", observable="density", dimension=2, normalize_density=False)
        inputs = input_doc(state_row)
        inputs["cases"].append(density_row)
        inputs["cross_checks"] = [{"kind": "pure_density", "density_case": "density", "state_case": "evolve"}]
        result = result_doc(state_row)
        psi = validate.states(result["cases"][0])
        rho = np.array([np.outer(state, state.conj()).reshape(-1, order="F") for state in psi])
        result["cases"].extend(from_states(density_row, rho)["cases"])
        report = oracle.evaluate(inputs, result, RUBRIC)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["cross_checks"][0]["common_times"], 3)


class HamiltonianIndependenceTests(unittest.TestCase):
    def test_xxz_against_tensor_product_operators(self):
        length, delta = 4, 0.7
        sx = np.array([[0, 1], [1, 0]]) / 2
        sy = np.array([[0, -1j], [1j, 0]]) / 2
        sz = np.diag([0.5, -0.5])
        reference = np.zeros((16, 16), dtype=complex)
        for site in range(length):
            for local, coefficient in ((sx, 1.0), (sy, 1.0), (sz, delta)):
                term = np.array([[1.0]])
                for position in range(length):
                    term = np.kron(term, local if position in (site, (site + 1) % length) else np.eye(2))
                reference += coefficient * term
        actual = oracle.xxz_matrix({"kind": "xxz", "L": length, "delta": delta, "flip": 0.5, "periodic": True})
        np.testing.assert_allclose(actual, reference, atol=2e-15, rtol=0)

    def test_sector_projection_and_l12_size(self):
        length = 6
        groups = oracle.rotation_orbits(length, 3)
        projection = np.zeros((1 << length, len(groups)))
        for column, group in enumerate(groups):
            projection[group, column] = 1 / np.sqrt(len(group))
        np.testing.assert_allclose(projection.T @ projection, np.eye(len(groups)), atol=1e-15)
        spec = {"kind": "xxz", "L": length, "delta": 0.5, "flip": 1.0}
        full = oracle.xxz_matrix(spec)
        reduced = oracle.xxz_matrix(dict(spec, kind="xxz_sector", N=3))
        np.testing.assert_allclose(reduced, projection.T @ full @ projection, atol=2e-15, rtol=0)
        self.assertEqual(len(oracle.rotation_orbits(12, 6)), 80)
        self.assertEqual(sum(map(len, oracle.rotation_orbits(12, 6))), 924)


class PairPolicyTests(unittest.TestCase):
    def test_pair_metric_is_not_algorithm_error(self):
        row = case()
        result = result_doc(row)
        pair = validate.pair_evaluate(result, result, input_doc(row), input_doc(row), RUBRIC)
        self.assertTrue(pair["passed"])
        self.assertEqual(pair["distance"], 0.0)
        self.assertEqual(pair["bound_fraction"], 0.0)

    def test_complex_magnitude_not_separate_components(self):
        row = case()
        reference, candidate = result_doc(row), result_doc(row)
        candidate["cases"][0]["states_real"][0][1] += 0.8e-10
        candidate["cases"][0]["states_imag"][0][1] += 0.8e-10
        report = validate.pair_evaluate(reference, candidate, input_doc(row), input_doc(row), RUBRIC)
        self.assertFalse(report["passed"])
        self.assertAlmostEqual(report["bound_fraction"], np.sqrt(2) * 0.8)

    def test_pair_case_override_and_invalid_bounds(self):
        row = case()
        reference, candidate = result_doc(row), result_doc(row)
        candidate["cases"][0]["states_real"][1][0] += 2e-9
        rubric = copy.deepcopy(RUBRIC)
        rubric["comparison"]["case_overrides"] = {"evolve": {"atol": 1e-8, "rtol": 0.0}}
        report = validate.pair_evaluate(reference, candidate, input_doc(row), input_doc(row), rubric)
        self.assertTrue(report["passed"])
        self.assertAlmostEqual(report["bound_fraction"], 0.2, places=7)
        for bad in (-1, float("nan"), float("inf"), True):
            rubric["comparison"]["case_overrides"]["evolve"]["atol"] = bad
            with self.assertRaises(ValueError):
                validate.pair_evaluate(reference, candidate, input_doc(row), input_doc(row), rubric)
        rubric["comparison"]["case_overrides"] = {"typo": {"atol": 1e-8}}
        with self.assertRaises(ValueError):
            validate.pair_evaluate(reference, candidate, input_doc(row), input_doc(row), rubric)

    def test_missing_case_rejected(self):
        row = case()
        result = result_doc(row)
        empty = dict(result, cases=[])
        with self.assertRaises(ValueError):
            validate.pair_evaluate(result, empty, input_doc(row), input_doc(row), RUBRIC)

    def test_discrete_api_exact_policy(self):
        inputs = input_doc({"id": "api", "mode": "api", "expected_statuses": {"old_keyword": "MethodError"}})
        result = {"schema_version": 1, "check": "synthetic", "cases": [{"id": "api", "statuses": {"old_keyword": "MethodError"}}]}
        rubric = {"policy": "invariants", "comparison": {"scientific": {}}}
        report = validate.pair_evaluate(result, result, inputs, inputs, rubric)
        self.assertTrue(report["passed"])
        self.assertEqual(report["policy"], "invariants")
        bad = copy.deepcopy(result)
        bad["cases"][0]["statuses"]["old_keyword"] = "no_error"
        with self.assertRaises(ValueError):
            validate.pair_evaluate(result, bad, inputs, inputs, rubric)

    def test_broad_diagnostics_not_exact_counts(self):
        row = case()
        row["diagnostic_requirements"] = {"restarts": {"min": 1}, "max_dim_used": {"max": 20}}
        reference, candidate = result_doc(row), result_doc(row)
        reference["cases"][0]["diagnostics"] = {"restarts": 2, "max_dim_used": 10}
        candidate["cases"][0]["diagnostics"] = {"restarts": 3, "max_dim_used": 11}
        self.assertTrue(validate.pair_evaluate(reference, candidate, input_doc(row), input_doc(row), RUBRIC)["passed"])
        candidate["cases"][0]["diagnostics"]["restarts"] = 0
        with self.assertRaises(ValueError):
            validate.pair_evaluate(reference, candidate, input_doc(row), input_doc(row), RUBRIC)

    def test_shortening_is_trusted_environment_only(self):
        row = case()
        short = result_doc(row, scale=0.5)
        with patch.dict(os.environ, {"SAB_TIME_SCALE": "0.5"}):
            self.assertTrue(validate.pair_evaluate(short, short, input_doc(row), input_doc(row), RUBRIC)["passed"])
        with self.assertRaises(ValueError):
            validate.pair_evaluate(short, short, input_doc(row), input_doc(row), RUBRIC)
        for bad in ("nan", "inf", "0", "-1", "1.1"):
            with patch.dict(os.environ, {"SAB_TIME_SCALE": bad}):
                with self.assertRaises(ValueError):
                    validate.pair_evaluate(short, short, input_doc(row), input_doc(row), RUBRIC)


if __name__ == "__main__":
    unittest.main()

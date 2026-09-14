#!/usr/bin/env python3
"""Independent matrix-descriptor observables copied into each check."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.build import molecule
from dscribe.descriptors import CoulombMatrix, EwaldSumMatrix, SineMatrix


def flat(*arrays):
    return np.concatenate([np.asarray(a, dtype=np.float64).ravel() for a in arrays])


def finite(value=1.0):
    return Atoms(
        "HCO",
        positions=[[0.12, 0.18, 0.22], [1.15 * value, 0.31, 0.44], [0.38, 1.27, 0.73]],
        cell=[[5.2, 0.2, 0.1], [0.1, 5.7, 0.3], [0.2, 0.1, 6.1]],
    )


def periodic(value=1.0):
    s = finite(value)
    s.set_pbc(True)
    return s


def moved(system, rotate_cell=False):
    theta = 0.417
    rot = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
    out = system.copy()
    out.positions = system.positions @ rot.T + [0.33, -0.27, 0.19]
    if rotate_cell:
        out.set_cell(np.asarray(system.cell) @ rot.T)
    return out


def cm(permutation="none", **kwargs):
    return CoulombMatrix(n_atoms_max=5, permutation=permutation, **kwargs)


def sm(permutation="none", **kwargs):
    return SineMatrix(n_atoms_max=5, permutation=permutation, **kwargs)


def em(permutation="none", **kwargs):
    return EwaldSumMatrix(n_atoms_max=5, permutation=permutation, **kwargs)


def matrix2(desc, system, **kwargs):
    return desc.unflatten(desc.create(system, **kwargs))


def coulomb_python(system, nmax=5):
    pos = system.positions
    q = system.numbers.astype(float)
    dist = np.linalg.norm(pos[:, None] - pos[None, :], axis=-1)
    np.fill_diagonal(dist, 1.0)
    mat = q[:, None] * q[None, :] / dist
    np.fill_diagonal(mat, 0.5 * q**2.4)
    out = np.zeros((nmax, nmax))
    out[: len(system), : len(system)] = mat
    return out


def sine_python(system, nmax=5):
    pos = system.positions
    cell = np.asarray(system.cell)
    delta = pos[:, None, :] - pos[None, :, :]
    arg = np.pi * np.dot(delta, np.linalg.inv(cell))
    phi = np.linalg.norm(np.dot(np.sin(arg) ** 2, cell), axis=2)
    with np.errstate(divide="ignore"):
        invphi = 1.0 / phi
    q = system.numbers.astype(float)
    mat = q[:, None] * q[None, :] * invphi
    np.fill_diagonal(mat, 0.5 * q**2.4)
    out = np.zeros((nmax, nmax))
    out[: len(system), : len(system)] = mat
    return out


def sorted_observable(desc, system, **kwargs):
    raw = matrix2(type(desc)(n_atoms_max=5, permutation="none"), system, **kwargs)
    n = len(system)
    core = raw[:n, :n]
    order = np.argsort(-np.linalg.norm(core, axis=1), kind="stable")
    manual = np.zeros_like(raw)
    manual[:n, :n] = core[order][:, order]
    actual = matrix2(desc, system, **kwargs)
    return flat(actual, manual, actual - manual)


def eigen_observable(cls, system, **kwargs):
    raw = matrix2(cls(n_atoms_max=5, permutation="none"), system, **kwargs)[: len(system), : len(system)]
    values = np.linalg.eigvalsh(raw)
    manual = values[np.argsort(np.abs(values))[::-1]]
    manual = np.pad(manual, (0, 5 - len(manual)))
    actual = cls(n_atoms_max=5, permutation="eigenspectrum").create(system, **kwargs)
    return flat(actual, manual, actual - manual)


def random_statistics(cls, system, **kwargs):
    desc = cls(n_atoms_max=5, permutation="random", sigma=2.0, seed=42)
    counts = np.zeros((len(system), len(system)))
    diagonals = 0.5 * system.numbers.astype(float) ** 2.4
    for _ in range(128):
        diag = np.diag(desc.unflatten(desc.create(system, **kwargs)))[: len(system)]
        identities = np.argmin(np.abs(diag[:, None] - diagonals[None, :]), axis=1)
        for rank, atom in enumerate(identities):
            counts[rank, atom] += 1
    raw = matrix2(cls(n_atoms_max=5, permutation="none"), system, **kwargs)[: len(system), : len(system)]
    return flat(counts / 128.0, np.linalg.norm(raw, axis=1))


def parallel_observable(cls, systems, **kwargs):
    desc = cls(n_atoms_max=5, permutation="none")
    a = desc.create(systems, n_jobs=1, **kwargs)
    b = desc.create(systems, n_jobs=2, **kwargs)
    return flat(a, b, b - a)


def derivative_observable(desc, system):
    d, f = desc.derivatives(system, method="numerical")
    return flat(d, f)


def coulomb_sorted_matrix(value, repeats):
    x = sorted_observable(cm("sorted_l2"), finite(value))
    return flat(*([x] * repeats))


def coulomb_eigenspectrum(value, repeats):
    x = eigen_observable(CoulombMatrix, finite(value))
    return flat(*([x] * repeats))


def coulomb_random_permutation(value, repeats):
    x = random_statistics(CoulombMatrix, finite(value))
    return flat(*([x] * repeats))


def coulomb_parallel_create(value, repeats):
    x = parallel_observable(CoulombMatrix, [finite(value), molecule("H2O")])
    return flat(*([x] * repeats))


def coulomb_symmetries(value, repeats):
    s = finite(value); t = moved(s)
    a, b = cm().create(s), cm().create(t)
    e, ep = cm("eigenspectrum").create(s), cm("eigenspectrum").create(s[[2, 0, 1]])
    return flat(*((a, b, b - a, e, ep, ep - e) * repeats))


def coulomb_numerical_derivatives(value, repeats):
    return flat(*([derivative_observable(cm(), finite(value)), derivative_observable(cm("eigenspectrum"), finite(value))] * repeats))


def coulomb_reference_formula(value, repeats):
    s = finite(value); a = matrix2(cm(), s); b = coulomb_python(s)
    return flat(*((a, b, a - b) * repeats))


def coulomb_finite_distance(value, repeats):
    s = finite(value); p = s.copy(); p.set_pbc(True)
    a, b = cm().create(s), cm().create(p)
    return flat(*((a, b, b - a) * repeats))


def coulomb_standard_example(value, repeats):
    s = molecule("H2O"); s.positions[1] *= value
    return flat(*((cm().create(s), cm("sorted_l2").create(s), cm("eigenspectrum").create(s)) * repeats))


def sine_sorted_matrix(value, repeats):
    x = sorted_observable(sm("sorted_l2"), periodic(value)); return flat(*([x] * repeats))


def sine_eigenspectrum(value, repeats):
    x = eigen_observable(SineMatrix, periodic(value)); return flat(*([x] * repeats))


def sine_random_permutation(value, repeats):
    x = random_statistics(SineMatrix, periodic(value)); return flat(*([x] * repeats))


def sine_parallel_create(value, repeats):
    x = parallel_observable(SineMatrix, [periodic(value), periodic(value + 0.02)]); return flat(*([x] * repeats))


def sine_symmetries(value, repeats):
    s = periodic(value); t = moved(s, rotate_cell=True)
    a, b = sm().create(s), sm().create(t)
    e, ep = sm("eigenspectrum").create(s), sm("eigenspectrum").create(s[[2, 0, 1]])
    return flat(*((a, b, b - a, e, ep, ep - e) * repeats))


def sine_numerical_derivatives(value, repeats):
    return flat(*([derivative_observable(sm(), periodic(value)), derivative_observable(sm("eigenspectrum"), periodic(value))] * repeats))


def sine_periodic_formula(value, repeats):
    s = periodic(value); a = matrix2(sm(), s); b = sine_python(s)
    return flat(*((a, b, a - b) * repeats))


def sine_unit_cells(value, repeats):
    s = periodic(value); outputs = []
    for cell in ([20, 30, 40], [3, 3.5, 4], [[0, 3, 3], [3, 0, 3], [3, 3, 0]]):
        q = s.copy(); q.set_cell(cell); outputs.append(sm().create(q))
    return flat(*(outputs * repeats))


def sine_standard_example(value, repeats):
    s = periodic(value); return flat(*((sm().create(s), sm("sorted_l2").create(s), sm("eigenspectrum").create(s)) * repeats))


def ewald_kwargs():
    return {"accuracy": 1e-4}


def ewald_sorted_matrix(value, repeats):
    x = sorted_observable(em("sorted_l2"), periodic(value), **ewald_kwargs()); return flat(*([x] * repeats))


def ewald_eigenspectrum(value, repeats):
    x = eigen_observable(EwaldSumMatrix, periodic(value), **ewald_kwargs()); return flat(*([x] * repeats))


def ewald_random_permutation(value, repeats):
    x = random_statistics(EwaldSumMatrix, periodic(value), **ewald_kwargs()); return flat(*([x] * repeats))


def ewald_parallel_create(value, repeats):
    x = parallel_observable(EwaldSumMatrix, [periodic(value), periodic(value + 0.02)], **ewald_kwargs()); return flat(*([x] * repeats))


def ewald_symmetries(value, repeats):
    s = periodic(value); t = moved(s, rotate_cell=True)
    a, b = em().create(s, **ewald_kwargs()), em().create(t, **ewald_kwargs())
    e, ep = em("eigenspectrum").create(s, **ewald_kwargs()), em("eigenspectrum").create(s[[2, 0, 1]], **ewald_kwargs())
    return flat(*((a, b, b - a, e, ep, ep - e) * repeats))


def ewald_numerical_derivatives(value, repeats):
    return flat(*([derivative_observable(em(), periodic(value)), derivative_observable(em("eigenspectrum"), periodic(value))] * repeats))


def ewald_automatic_cutoffs(value, repeats):
    s = periodic(value); outputs = [em().create(s, accuracy=a, w=w) for a, w in ((1e-3, 1), (1e-5, 1), (1e-5, 2))]
    return flat(*(outputs * repeats))


def ewald_screening_independence(value, repeats):
    s = periodic(value); outputs = [em().create(s, a=a, r_cut=10, g_cut=10) for a in (0.5, 0.8, 1.1)]
    outputs.extend((outputs[1] - outputs[0], outputs[2] - outputs[1]))
    return flat(*(outputs * repeats))


def ewald_electrostatic_reference(value, repeats):
    s = periodic(value); m = matrix2(em(), s, accuracy=1e-6); n = len(s); core = m[:n, :n]
    total = np.trace(core) + np.sum(np.triu(core, 1))
    pair = core + np.diag(core)[:, None] + np.diag(core)[None, :]
    return flat(*((m, np.array([total]), pair) * repeats))


def ewald_unit_cells(value, repeats):
    s = periodic(value); outputs = []
    for cell in ([8, 9, 10], [4, 4.5, 5], [[0, 4, 4], [4, 0, 4], [4, 4, 0]]):
        q = s.copy(); q.set_cell(cell); outputs.append(em().create(q, accuracy=1e-4))
    return flat(*(outputs * repeats))


def ewald_standard_example(value, repeats):
    s = periodic(value); return flat(*((em().create(s, accuracy=1e-4), em("sorted_l2").create(s, accuracy=1e-4), em("eigenspectrum").create(s, accuracy=1e-4)) * repeats))


FUNCTIONS = {name.replace("_", "-"): function for name, function in list(globals().items()) if callable(function) and name.startswith(("coulomb_", "sine_", "ewald_"))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True); parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=1); parser.add_argument("--check")
    args = parser.parse_args()
    value = float(json.loads(Path(args.input).read_text(encoding="utf-8"))["value"])
    check = args.check or Path(__file__).resolve().parent.name
    result = FUNCTIONS[check](value, args.repeats)
    if result.size == 0 or not np.all(np.isfinite(result)):
        raise RuntimeError("check produced an empty or non-finite observable")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out, result.astype(np.float64, copy=False), allow_pickle=False)


if __name__ == "__main__":
    main()

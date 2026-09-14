#!/usr/bin/env python3
"""Independent ACSF observables copied into every self-contained check."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.build import bulk, molecule
from dscribe.descriptors import ACSF


def flat(*arrays):
    return np.concatenate([np.asarray(array, dtype=np.float64).ravel() for array in arrays])


def water(value=1.0):
    return Atoms("OHH", positions=[[0.0, 0.0, 0.0], [value, 0.0, 0.0], [-0.24, 0.93, 0.0]])


def descriptor(**kwargs):
    args = dict(
        r_cut=4.0,
        species=["H", "C", "N", "O", "F"],
        g2_params=[[0.5, 0.0], [1.2, 1.0]],
        g3_params=[1.0, 2.0],
        g4_params=[[0.3, 1.0, 1.0]],
        g5_params=[[0.2, 2.0, -1.0]],
        dtype="float64",
    )
    args.update(kwargs)
    return ACSF(**args)


def parallel_centers(value, repeats):
    systems = [water(value), molecule("CO")]
    systems[1].positions[1, 0] += value - 1.0
    acsf = descriptor()
    outputs = []
    for _ in range(repeats):
        serial = acsf.create(systems, centers=[[0, 1], [0, 1]], n_jobs=1)
        parallel = acsf.create(systems, centers=[[0, 1], [0, 1]], n_jobs=2)
        deriv_s, feat_s = acsf.derivatives(systems, centers=[[0], [0]], n_jobs=1, attach=True)
        deriv_p, feat_p = acsf.derivatives(systems, centers=[[0], [0]], n_jobs=2, attach=True)
        outputs.extend((*serial, *parallel, *(np.asarray(a) - np.asarray(b) for a, b in zip(serial, parallel))))
        outputs.extend((*deriv_s, *deriv_p, *feat_s, *feat_p))
    return flat(*outputs)


def rigid_symmetries(value, repeats):
    system = water(value)
    theta = 0.731
    rotation = np.array([[np.cos(theta), -np.sin(theta), 0.0], [np.sin(theta), np.cos(theta), 0.0], [0.0, 0.0, 1.0]])
    moved = system.copy()
    moved.positions = system.positions @ rotation.T + [0.37, -0.22, 0.51]
    acsf = descriptor()
    original = acsf.create(system)
    changed = acsf.create(moved)
    return flat(*((original, changed, changed - original) * repeats))


def periodic_images(value, repeats):
    reference = Atoms("CC", positions=[[0, 0, 0], [-value, -1, -1]], cell=[[0, 10, 10], [10, 0, 10], [10, 10, 0]], pbc=False)
    periodic = reference.copy()
    periodic.pbc = True
    periodic.wrap()
    acsf = descriptor(periodic=True)
    a = acsf.create(reference)
    b = acsf.create(periodic)
    return flat(*((a, b, b - a) * repeats))


def environment_basis(value, repeats):
    systems = [
        Atoms("HO", positions=[[0, 0, 0], [value, 1, 1]], cell=[2, 2, 2], pbc=True),
        Atoms("OC", positions=[[0, 0, 0], [1, 1, 1]], cell=[2, 2, 2], pbc=True),
        Atoms("CN", positions=[[0, 0, 0], [1, 1, 1]], cell=[2, 2, 2], pbc=True),
    ]
    systems.append(systems[-1] * (2, 2, 2))
    acsf = descriptor(periodic=True)
    vectors = [acsf.create(system).mean(axis=0) for system in systems]
    normalized = [vector / np.linalg.norm(vector) for vector in vectors]
    dots = np.array([np.dot(normalized[0], normalized[2]), np.dot(normalized[0], normalized[1]), np.dot(normalized[2], normalized[3])])
    return flat(*((vectors + [dots]) * repeats))


def numerical_derivatives(value, repeats):
    system = molecule("CH3COF")
    system.positions[1, 0] += value - 1.0
    acsf = descriptor()
    outputs = []
    for _ in range(repeats):
        derivatives, features = acsf.derivatives(system, centers=[0, 1], method="numerical", attach=True)
        outputs.extend((derivatives, features))
    return flat(*outputs)


def cutoff(distance, r_cut):
    return 0.5 * (np.cos(np.pi * distance / r_cut) + 1.0)


def analytic_features(value, repeats):
    system = water(value)
    eta, shift, kappa, zeta, lambd, r_cut = np.sqrt(5), np.sqrt(2), np.sqrt(3), np.sqrt(7), 1.0, 6.0
    configurations = [
        ACSF(r_cut=r_cut, species=["H", "O"]),
        ACSF(r_cut=r_cut, species=["H", "O"], g2_params=[[eta, shift]]),
        ACSF(r_cut=r_cut, species=["H", "O"], g3_params=[kappa]),
        ACSF(r_cut=r_cut, species=["H", "O"], g4_params=[[eta, zeta, lambd]]),
        ACSF(r_cut=r_cut, species=["H", "O"], g5_params=[[eta, zeta, lambd]]),
    ]
    outputs = [desc.create(system) for desc in configurations]
    distances = system.get_all_distances()
    formula_inputs = np.array([distances[0, 1], distances[0, 2], distances[1, 2], cutoff(distances[0, 1], r_cut), cutoff(distances[1, 2], r_cut)])
    return flat(*((outputs + [formula_inputs]) * repeats))


def angular_cutoff(value, repeats):
    distance = 2.0 * value
    system = Atoms("HHH", positions=[[0, 0, 0], [distance, 0, 0], [0, distance, 0]])
    r_cut = 2.8
    desc = ACSF(r_cut=r_cut, species=["H"], g4_params=[[1, 1, 1]], g5_params=[[1, 1, 1]])
    features = desc.create(system, centers=[0])
    expected = np.array([2 * cutoff(distance, r_cut), 0.0, np.exp(-2 * distance**2) * cutoff(distance, r_cut) ** 2])
    return flat(*((features, expected, features.ravel() - expected) * repeats))


def periodic_coordination(value, repeats):
    single = Atoms("H", positions=[[0, 0, 0]], cell=[2 * value, 2, 2], pbc=True)
    radial = ACSF(r_cut=3.0, species=["H"], periodic=True).create(single)
    nacl = bulk("NaCl", "rocksalt", a=4 * value)
    angular = ACSF(r_cut=3.0, species=["Na", "Cl"], periodic=True, g4_params=[[0.01, 0.1, 1.0]]).create(nacl)
    return flat(*((radial, angular) * repeats))


def standard_example(value, repeats):
    system = water(value)
    acsf = ACSF(r_cut=6.0, species=["H", "O"], g2_params=[[1, 1], [1, 2], [1, 3]], g4_params=[[1, 1, 1], [1, 2, 1], [1, 1, -1], [1, 2, -1]])
    output = acsf.create(system, centers=[1])
    return flat(*(output for _ in range(repeats)))


FUNCTIONS = {
    "acsf-parallel-centers": parallel_centers,
    "acsf-rigid-symmetries": rigid_symmetries,
    "acsf-periodic-images": periodic_images,
    "acsf-environment-basis": environment_basis,
    "acsf-numerical-derivatives": numerical_derivatives,
    "acsf-analytic-features": analytic_features,
    "acsf-angular-cutoff": angular_cutoff,
    "acsf-periodic-coordination": periodic_coordination,
    "acsf-standard-example": standard_example,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--check")
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

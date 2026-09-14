#!/usr/bin/env python3
"""Independent MBTR-family observables copied into every self-contained check."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.build import bulk, molecule
from dscribe.descriptors import LMBTR, MBTR, ValleOganov


def flat(*arrays):
    return np.concatenate([np.asarray(array, dtype=np.float64).ravel() for array in arrays])


def finite(value=1.0):
    return Atoms(
        "OHH",
        positions=[[0, 0, 0], [value, 0, 0], [-0.24, 0.93, 0]],
        cell=[5.0, 5.0, 5.0],
    )


def k1(**kwargs):
    args = dict(species=["H", "O"], geometry={"function": "atomic_number"}, grid={"min": 1, "max": 8, "sigma": 0.1, "n": 50}, weighting={"function": "unity"}, dtype="float64")
    args.update(kwargs)
    return MBTR(**args)


def k2(**kwargs):
    args = dict(species=["H", "O"], geometry={"function": "inverse_distance"}, grid={"min": 0, "max": 1 / 0.7, "sigma": 0.1, "n": 50}, weighting={"function": "exp", "scale": 0.5, "threshold": 1e-2}, dtype="float64")
    args.update(kwargs)
    return MBTR(**args)


def k3(**kwargs):
    args = dict(species=["H", "O"], geometry={"function": "angle"}, grid={"min": 0, "max": 180, "sigma": 2, "n": 50}, weighting={"function": "exp", "scale": 0.5, "threshold": 1e-2}, dtype="float64")
    args.update(kwargs)
    return MBTR(**args)


def lk2(**kwargs):
    args = dict(species=["H", "O"], geometry={"function": "inverse_distance"}, grid={"min": 0, "max": 1 / 0.7, "sigma": 0.1, "n": 50}, weighting={"function": "exp", "scale": 0.5, "threshold": 1e-2}, dtype="float64")
    args.update(kwargs)
    return LMBTR(**args)


def lk3(**kwargs):
    args = dict(species=["H", "O"], geometry={"function": "angle"}, grid={"min": 0, "max": 180, "sigma": 2, "n": 50}, weighting={"function": "exp", "scale": 0.5, "threshold": 1e-2}, dtype="float64")
    args.update(kwargs)
    return LMBTR(**args)


def vo(function="distance", **kwargs):
    args = dict(species=["H", "O"], function=function, sigma=0.2, n=40, r_cut=4.0, dtype="float64")
    args.update(kwargs)
    return ValleOganov(**args)


def mbtr_parallel_create(value, repeats):
    systems = [finite(value), finite(value + 0.1)]
    descriptor = k2()
    outputs = []
    for _ in range(repeats):
        serial = descriptor.create(systems, n_jobs=1)
        parallel = descriptor.create(systems, n_jobs=2)
        d1, f1 = descriptor.derivatives(systems, n_jobs=1)
        d2, f2 = descriptor.derivatives(systems, n_jobs=2)
        outputs.extend((serial, parallel, parallel - serial, d1, d2, d2 - d1, f1, f2))
    return flat(*outputs)


def mbtr_k_body_bases(value, repeats):
    system = finite(value)
    outputs = []
    for _ in range(repeats):
        outputs.extend((k1().create(system), k2().create(system), k3().create(system)))
    return flat(*outputs)


def transformed(system):
    theta = 0.731
    rotation = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
    moved = system.copy()
    moved.positions = system.positions @ rotation.T + [0.37, -0.22, 0.51]
    return moved


def mbtr_rigid_symmetries(value, repeats):
    system = finite(value)
    moved = transformed(system)
    a, b = k2().create(system), k2().create(moved)
    return flat(*((a, b, b - a) * repeats))


def mbtr_analytical_derivatives(value, repeats):
    system = finite(value)
    outputs = []
    descriptors = [
        MBTR(species=["H", "O"], geometry={"function": "distance"}, grid={"min": 0, "max": 4, "sigma": 0.05, "n": 50}, weighting={"function": "exp", "r_cut": 4, "threshold": 1e-3}),
        MBTR(species=["H", "O"], geometry={"function": "cosine"}, grid={"min": -1, "max": 1, "sigma": 0.02, "n": 50}, weighting={"function": "exp", "scale": 0.5, "threshold": 1e-2}),
    ]
    for _ in range(repeats):
        for descriptor in descriptors:
            derivatives, features = descriptor.derivatives(system, method="analytical")
            outputs.extend((derivatives, features))
    return flat(*outputs)


def mbtr_numerical_derivatives(value, repeats):
    system = finite(value)
    outputs = []
    for _ in range(repeats):
        for descriptor in (k2(normalization="none"), k2(normalization="l2"), k3(normalization="n_atoms")):
            derivatives, features = descriptor.derivatives(system, method="numerical")
            outputs.extend((derivatives, features))
    return flat(*outputs)


def mbtr_valle_oganov_derivatives(value, repeats):
    system = bulk("NaCl", "rocksalt", a=5.64 * value)
    descriptor = MBTR(species=["Na", "Cl"], geometry={"function": "distance"}, grid={"min": 0, "max": 5, "sigma": 0.1, "n": 40}, weighting={"function": "inverse_square", "r_cut": 5}, periodic=True, normalization="valle_oganov")
    outputs = []
    for _ in range(repeats):
        for method in ("numerical", "analytical"):
            derivatives, features = descriptor.derivatives(system, method=method)
            outputs.extend((derivatives, features))
    return flat(*outputs)


def mbtr_normalization(value, repeats):
    system = bulk("Cu", "fcc", cubic=True, a=3.6 * value)
    outputs = []
    for _ in range(repeats):
        for normalization in ("none", "l2", "n_atoms", "valle_oganov"):
            outputs.append(k2(species=["Cu"], periodic=True, normalization=normalization).create(system))
    return flat(*outputs)


def mbtr_geometry_peaks(value, repeats):
    system = finite(value)
    descriptors = [
        k1(grid={"min": 0, "max": 10, "sigma": 0.1, "n": 100}),
        MBTR(species=["H", "O"], geometry={"function": "distance"}, grid={"min": 0, "max": 3, "sigma": 0.05, "n": 120}, weighting={"function": "unity"}),
        MBTR(species=["H", "O"], geometry={"function": "angle"}, grid={"min": 0, "max": 180, "sigma": 1, "n": 120}, weighting={"function": "unity"}),
    ]
    return flat(*([descriptor.create(system) for descriptor in descriptors] * repeats))


def mbtr_gaussian_distribution(value, repeats):
    system = Atoms("HH", positions=[[0, 0, 0], [value, 0, 0]])
    outputs = []
    for normalize in (False, True):
        descriptor = MBTR(species=["H"], geometry={"function": "distance"}, grid={"min": 0, "max": 2, "sigma": 0.1, "n": 200}, weighting={"function": "unity"}, normalize_gaussians=normalize)
        outputs.append(descriptor.create(system))
    return flat(*(outputs * repeats))


def periodic_pair(value):
    return Atoms("NaCl", scaled_positions=[[0, 0, 0], [0.5, 0.5, 0.5]], cell=[4.2 * value, 4.3, 4.4], pbc=True)


def mbtr_periodic_translation(value, repeats):
    system = periodic_pair(value)
    shifted = system.copy()
    shifted.positions += system.cell[0]
    outputs = []
    for descriptor in (k2(species=["Na", "Cl"], periodic=True), k3(species=["Na", "Cl"], periodic=True)):
        a, b = descriptor.create(system), descriptor.create(shifted)
        outputs.extend((a, b, b - a))
    return flat(*(outputs * repeats))


def mbtr_supercell_similarity(value, repeats):
    primitive = bulk("NaCl", "rocksalt", a=5.64 * value)
    supercell = primitive * (2, 2, 2)
    outputs = []
    descriptors = (
        MBTR(species=["Na", "Cl"], geometry={"function": "distance"}, grid={"min": 0, "max": 5, "sigma": 0.1, "n": 50}, weighting={"function": "inverse_square", "r_cut": 5}, periodic=True, normalization="l2"),
        MBTR(species=["Na", "Cl"], geometry={"function": "angle"}, grid={"min": 0, "max": 180, "sigma": 2, "n": 50}, weighting={"function": "smooth_cutoff", "r_cut": 5}, periodic=True, normalization="l2"),
    )
    for descriptor in descriptors:
        a, b = descriptor.create(primitive), descriptor.create(supercell)
        outputs.extend((a, b, b - a))
    return flat(*(outputs * repeats))


def mbtr_periodic_images(value, repeats):
    system = Atoms("HH", positions=[[0, 0, 0], [value, 0, 0]], cell=[2, 2, 2], pbc=True)
    outputs = []
    for descriptor in (k2(species=["H"], periodic=True), k3(species=["H"], periodic=True)):
        outputs.append(descriptor.create(system))
    return flat(*(outputs * repeats))


def lmbtr_parallel_centers(value, repeats):
    systems = [finite(value), finite(value + 0.1)]
    descriptor = lk2()
    outputs = []
    for _ in range(repeats):
        serial = descriptor.create(systems, centers=[[0, 1], [0]], n_jobs=1)
        parallel = descriptor.create(systems, centers=[[0, 1], [0]], n_jobs=2)
        outputs.extend((*serial, *parallel, *(np.asarray(b) - np.asarray(a) for a, b in zip(serial, parallel))))
    return flat(*outputs)


def lmbtr_k_body_bases(value, repeats):
    system = finite(value)
    return flat(*(([lk2().create(system, centers=[0, 1]), lk3().create(system, centers=[0, 1])]) * repeats))


def lmbtr_rigid_symmetries(value, repeats):
    system = finite(value)
    moved = transformed(system)
    a, b = lk2().create(system, centers=[0, 1]), lk2().create(moved, centers=moved.positions[[0, 1]])
    return flat(*((a, b, b - a) * repeats))


def lmbtr_numerical_derivatives(value, repeats):
    system = finite(value)
    outputs = []
    for attach in (True, False):
        derivatives, features = lk2().derivatives(system, centers=[0, 1], method="numerical", attach=attach)
        outputs.extend((derivatives, features))
    return flat(*(outputs * repeats))


def lmbtr_normalization(value, repeats):
    system = bulk("Cu", "fcc", cubic=True, a=3.6 * value)
    descriptor = lk2(species=["Cu"], periodic=True, normalization="l2")
    output = descriptor.create(system, centers=[0, 1])
    norms = np.linalg.norm(output, axis=1)
    return flat(*((output, norms) * repeats))


def lmbtr_geometry_peaks(value, repeats):
    system = finite(value)
    d2 = LMBTR(species=["H", "O"], geometry={"function": "distance"}, grid={"min": 0, "max": 3, "sigma": 0.05, "n": 120}, weighting={"function": "unity"})
    d3 = LMBTR(species=["H", "O"], geometry={"function": "angle"}, grid={"min": 0, "max": 180, "sigma": 1, "n": 120}, weighting={"function": "unity"})
    return flat(*((d2.create(system, centers=[0, 1]), d3.create(system, centers=[0, 1])) * repeats))


def valle_oganov_parallel_create(value, repeats):
    systems = [periodic_pair(value), periodic_pair(value + 0.01)]
    descriptor = vo(species=["Na", "Cl"])
    outputs = []
    for _ in range(repeats):
        a, b = descriptor.create(systems, n_jobs=1), descriptor.create(systems, n_jobs=2)
        outputs.extend((a, b, b - a))
    return flat(*outputs)


def valle_oganov_symmetries(value, repeats):
    system = periodic_pair(value)
    moved = transformed(system)
    moved.set_cell(system.cell)
    descriptor = vo(species=["Na", "Cl"])
    a, b = descriptor.create(system), descriptor.create(moved)
    return flat(*((a, b, b - a) * repeats))


def valle_oganov_numerical_derivatives(value, repeats):
    system = finite(value)
    derivatives, features = vo().derivatives(system, method="numerical")
    return flat(*((derivatives, features) * repeats))


def valle_oganov_analytical_derivatives(value, repeats):
    system = finite(value)
    derivatives, features = vo().derivatives(system, method="analytical")
    return flat(*((derivatives, features) * repeats))


def valle_oganov_vs_mbtr(value, repeats):
    system = periodic_pair(value)
    outputs = []
    for function in ("distance", "angle"):
        sigma, n, cutoff = 0.1, 40, 5.0
        valle = vo(function, species=["Na", "Cl"], sigma=sigma, n=n, r_cut=cutoff)
        geometry = {"function": function}
        grid = {"min": 0, "max": cutoff if function == "distance" else 180, "sigma": sigma, "n": n}
        weighting = {"function": "inverse_square", "r_cut": cutoff} if function == "distance" else {"function": "smooth_cutoff", "r_cut": cutoff}
        mbtr = MBTR(species=["Na", "Cl"], geometry=geometry, grid=grid, weighting=weighting, periodic=True, normalization="valle_oganov")
        a, b = valle.create(system), mbtr.create(system)
        outputs.extend((a, b, b - a))
    return flat(*(outputs * repeats))


def mbtr_standard_example(value, repeats):
    system = finite(value)
    nacl = periodic_pair(value)
    outputs = [k2().create(system), k3().create(system), k2(species=["Na", "Cl"], periodic=True).create(nacl)]
    return flat(*(outputs * repeats))


def lmbtr_standard_example(value, repeats):
    system = finite(value)
    outputs = [lk2().create(system, centers=[0]), lk3().create(system, centers=[[0.2, 0.1, value]])]
    return flat(*(outputs * repeats))


def valle_oganov_standard_example(value, repeats):
    system = periodic_pair(value)
    outputs = [vo("distance", species=["Na", "Cl"]).create(system), vo("angle", species=["Na", "Cl"]).create(system)]
    return flat(*(outputs * repeats))


FUNCTIONS = {
    name.replace("_", "-"): function
    for name, function in list(globals().items())
    if callable(function) and (name.startswith("mbtr_") or name.startswith("lmbtr_") or name.startswith("valle_oganov_"))
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

#!/usr/bin/env python3
"""Independent SOAP observables used by each self-contained check copy."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from ase import Atoms
from dscribe.descriptors import SOAP
from joblib import parallel_backend


def flat(*arrays):
    return np.concatenate([np.asarray(a, dtype=np.float64).ravel() for a in arrays])


def molecule(value=1.0):
    return Atoms(
        symbols=["O", "H", "H", "C"],
        positions=[[0.0, 0.0, 0.0], [value, 0.0, 0.0], [-0.24, 0.93, 0.0], [0.2, -0.3, 1.15]],
    )


def descriptor(**kwargs):
    args = dict(species=["H", "C", "O"], r_cut=3.5, n_max=3, l_max=3, sigma=0.45, dtype="float64")
    args.update(kwargs)
    return SOAP(**args)


def high_l_setup(rbf, value):
    limit = 20 if rbf == "gto" else 9
    x, y, z = np.meshgrid(np.arange(-1, 2), np.arange(-1, 2), np.arange(-1, 2))
    positions = np.column_stack((x.ravel(), y.ravel(), z.ravel())).astype(float)
    positions += np.random.RandomState(42).random((27, 3)) - 0.5
    positions[13] = [0.0, 0.0, 0.0]
    positions[0, 0] += value - 1.0
    system = Atoms(symbols=["H"] * len(positions), positions=positions)
    soap = SOAP(species=["H"], r_cut=2.0, n_max=1, l_max=limit, sigma=0.1,
                rbf=rbf, compression={"mode": "crossover"}, dtype="float64")
    return soap, system


def parallel_centers(value, repeats):
    systems = [molecule(value), molecule(value + 0.17)]
    soap = descriptor()
    outputs = []
    for _ in range(repeats):
        with parallel_backend("threading"):
            for n in (1, 2):
                outputs.extend(soap.create(systems, centers=[[0, 1], [0, 2]], n_jobs=n))
                outputs.extend(soap.create(systems, centers=[[[0, 0, 0], [value, 0, 0]], [[0, 0, 0]]], n_jobs=n))
    return flat(*outputs)


def rigid_symmetries(value, repeats):
    system = molecule(value)
    theta = 0.731
    rotation = np.array([[np.cos(theta), -np.sin(theta), 0.0], [np.sin(theta), np.cos(theta), 0.0], [0.0, 0.0, 1.0]])
    transformed = system.copy()
    transformed.positions = system.positions @ rotation.T + np.array([0.37, -0.22, 0.51])
    outputs = []
    for rbf in ("gto", "polynomial"):
        soap = descriptor(rbf=rbf)
        original = soap.create(system)
        changed = soap.create(transformed)
        outputs.extend((original, changed, changed - original))
    return flat(*(outputs * repeats))


def periodic_images(value, repeats):
    system = Atoms("NaClNaCl", positions=[[0, 0, 0], [1.4, 1.4, 1.4], [2.8, 0, 0], [1.4, 2.8, 1.4]], cell=[4.2, 4.2, 4.2], pbc=True)
    system.positions[1, 0] = value
    translated = system.copy()
    translated.positions += [4.2, 0, 0]
    soap = SOAP(species=["Na", "Cl"], r_cut=3.0, n_max=3, l_max=3, sigma=0.5, periodic=True, dtype="float64")
    outputs = []
    for _ in range(repeats):
        a, b = soap.create(system), soap.create(translated)
        outputs.extend((a, b, b - a))
    return flat(*outputs)


def center_modes(value, repeats):
    system = molecule(value)
    soap = descriptor()
    indices = soap.create(system, centers=[0, 1])
    cartesian = soap.create(system, centers=system.positions[[0, 1]])
    external = soap.create(system, centers=[[0.25, 0.25, value]])
    return flat(*((indices, cartesian, cartesian - indices, external) * repeats))


def radial_bases(value, repeats):
    system = molecule(value)
    outputs = []
    for _ in range(repeats):
        for rbf in ("gto", "polynomial"):
            outputs.append(descriptor(rbf=rbf).create(system, centers=[0, 1]))
    return flat(*outputs)


def numerical_derivatives(value, repeats):
    system = molecule(value)
    outputs = []
    for _ in range(repeats):
        for average, compression in (("off", "off"), ("off", "mu1nu1"), ("inner", "off"), ("outer", "crossover")):
            soap = descriptor(average=average, compression={"mode": compression})
            deriv, values = soap.derivatives(system, centers=[0, 1], method="numerical", attach=True)
            outputs.extend((deriv, values))
    return flat(*outputs)


def analytical_derivatives(value, repeats):
    system = molecule(value)
    outputs = []
    for _ in range(repeats):
        for mode in ("off", "crossover"):
            soap = descriptor(rbf="gto", average="off", periodic=False, compression={"mode": mode})
            for attach in (True, False):
                deriv, values = soap.derivatives(system, centers=[0, 1], method="analytical", attach=attach)
                outputs.extend((deriv, values))
    return flat(*outputs)


def crossover_compression(value, repeats):
    system = molecule(value)
    outputs = []
    for _ in range(repeats):
        for rbf in ("gto", "polynomial"):
            for mode in ("off", "crossover"):
                outputs.append(descriptor(rbf=rbf, compression={"mode": mode}).create(system, centers=[0, 1]))
    return flat(*outputs)


def outer_average(value, repeats):
    system = molecule(value)
    outputs = []
    for rbf in ("gto", "polynomial"):
        averaged = descriptor(rbf=rbf, average="outer").create(system, centers=[0, 1])
        individual = descriptor(rbf=rbf, average="off").create(system, centers=[0, 1])
        outputs.extend((averaged, individual.mean(axis=0), averaged - individual.mean(axis=0)))
    return flat(*(outputs * repeats))


def mu1nu1_compression(value, repeats):
    system = molecule(value)
    outputs = []
    for _ in range(repeats):
        for rbf in ("gto", "polynomial"):
            outputs.append(descriptor(rbf=rbf, compression={"mode": "mu1nu1"}).create(system, centers=[0, 1]))
    return flat(*outputs)


def inner_average(value, repeats):
    system = molecule(value)
    outputs = []
    for _ in range(repeats):
        for rbf in ("gto", "polynomial"):
            outputs.append(descriptor(rbf=rbf, average="inner").create(system, centers=[0, 1, 2]))
    return flat(*outputs)


def coefficient_integration(value, repeats):
    outputs = []
    for _ in range(repeats):
        for rbf in ("gto", "polynomial"):
            soap, system = high_l_setup(rbf, value)
            outputs.append(soap.create(system, centers=[[0.0, 0.0, 0.0]]))
    return flat(*outputs)


def weighting_functions(value, repeats):
    system = molecule(value)
    weights = [
        {"function": "poly", "r0": 3.0, "c": 2.0, "m": 3.0},
        {"function": "pow", "r0": 1.0, "c": 1.0, "d": 1.0, "m": 3.0},
        {"function": "exp", "r0": 1.5, "c": 2.0, "d": 1.0},
    ]
    outputs = []
    for _ in range(repeats):
        for rbf in ("gto", "polynomial"):
            for weighting in weights:
                outputs.append(descriptor(rbf=rbf, weighting=weighting).create(system, centers=[0, 1]))
    return flat(*outputs)


def periodic_padding(value, repeats):
    outputs = []
    rng = np.random.RandomState(7)
    for repeat in range(repeats):
        for ncells, r_cut, sigma in ((1, 2.2, 0.5), (2, 4.0, 1.0), (3, 5.5, 1.5)):
            a = 2.993
            system = Atoms("NiTi", positions=[[0, 0, 0], [a / 2, a / 2, a / 2]], cell=[a, a, a], pbc=True) * ncells
            noise = rng.normal(scale=0.1, size=system.positions.shape)
            noise[0, 0] += value - 1.0
            system.positions += noise
            system.wrap()
            soap = SOAP(species=["Ni", "Ti"], r_cut=r_cut, n_max=3, l_max=3, sigma=sigma, periodic=True, dtype="float64")
            orthogonal = soap.create(system)
            length = a * ncells
            skewed = system.copy()
            skewed.set_cell([[length, 0, 0], [0, length, 0], [length, 0, length]])
            skewed.wrap()
            monoclinic = soap.create(skewed)
            outputs.extend((orthogonal, monoclinic, monoclinic - orthogonal))
    return flat(*outputs)


def rbf_orthonormality(value, repeats):
    sigma = 0.15
    r_cut = 2.0 * value
    soap = SOAP(species=["H"], r_cut=r_cut, n_max=2, l_max=20, sigma=sigma, sparse=False)
    alphas = np.reshape(soap._alphas, [21, 2])
    betas = np.reshape(soap._betas, [21, 2, 2])
    extent = r_cut + 5.0
    rspace = np.linspace(0, extent, 10000)
    overlaps = []
    for l in range(21):
        functions = []
        for n in range(2):
            gto = sum(betas[l, n, k] * rspace**l * np.exp(-alphas[l, k] * rspace**2) for k in range(2))
            functions.append(gto)
        overlaps.append([[np.trapezoid(rspace**2 * functions[i] * functions[j], dx=extent / 10000) for j in range(2)] for i in range(2)])
    return flat(*([alphas, betas, np.asarray(overlaps)] * repeats))


def standard_example(value, repeats):
    water = Atoms("H2O", positions=[[0.0, 0.0, 0.0], [value, 0.0, 0.0], [-0.24, 0.93, 0.0]])
    methanol = Atoms("CH4O", positions=[[0, 0, 0], [1.42, 0, 0], [-0.63, 0.9, 0], [-0.63, -0.45, 0.78], [-0.63, -0.45, -0.78], [1.78, 0.6, 0]])
    peroxide = Atoms("H2O2", positions=[[-0.7, 0, 0], [0.7, 0, 0], [-1.1, 0.8, 0], [1.1, -0.8, 0]])
    soap = descriptor(average="outer")
    outputs = []
    for _ in range(repeats):
        vectors = np.vstack([soap.create(x) for x in (water, methanol, peroxide)])
        distances = np.linalg.norm(vectors[:, None, :] - vectors[None, :, :], axis=2)
        outputs.extend((vectors, distances))
    return flat(*outputs)


FUNCTIONS = {
    "parallel-centers": parallel_centers,
    "rigid-symmetries": rigid_symmetries,
    "periodic-images": periodic_images,
    "center-modes": center_modes,
    "radial-bases": radial_bases,
    "numerical-derivatives": numerical_derivatives,
    "analytical-derivatives": analytical_derivatives,
    "crossover-compression": crossover_compression,
    "outer-average": outer_average,
    "mu1nu1-compression": mu1nu1_compression,
    "inner-average": inner_average,
    "coefficient-integration": coefficient_integration,
    "weighting-functions": weighting_functions,
    "periodic-padding": periodic_padding,
    "rbf-orthonormality": rbf_orthonormality,
    "standard-example": standard_example,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    value = float(json.loads(Path(args.input).read_text())["value"])
    check = Path(__file__).resolve().parent.name
    result = FUNCTIONS[check](value, args.repeats)
    if result.size == 0 or not np.all(np.isfinite(result)):
        raise RuntimeError("check produced an empty or non-finite observable")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out, result.astype(np.float64, copy=False), allow_pickle=False)


if __name__ == "__main__":
    main()

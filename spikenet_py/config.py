from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import h5py
import numpy as np


@dataclass
class PopulationConfig:
    index: int
    size: int
    params: dict[str, float] = field(default_factory=dict)
    seed: int | None = None
    init_r_v0: float | None = None
    init_p_fire: float | None = None
    init_v_external: np.ndarray | None = None


@dataclass
class SynapseConfig:
    index: int
    syn_type: int
    pop_pre: int
    pop_post: int
    i: np.ndarray
    j: np.ndarray
    k: np.ndarray
    d: np.ndarray


@dataclass
class SimulationConfig:
    input_path: str
    dt: float
    step_tot: int
    pop_sizes: list[int]
    populations: list[PopulationConfig]
    synapses: list[SynapseConfig]


def _has_path(h5: h5py.File, path: str) -> bool:
    return path in h5


def _read_scalar(h5: h5py.File, path: str, cast: type, default: Any | None = None) -> Any:
    if not _has_path(h5, path):
        if default is not None:
            return default
        raise KeyError(f"Missing HDF5 path: {path}")
    value = h5[path][()]
    if isinstance(value, np.ndarray):
        value = value.reshape(-1)[0]
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return cast(value)


def _read_vector(h5: h5py.File, path: str, dtype: np.dtype) -> np.ndarray:
    if not _has_path(h5, path):
        raise KeyError(f"Missing HDF5 path: {path}")
    return np.asarray(h5[path][()]).reshape(-1).astype(dtype)


def _parse_para_ascii(raw_ascii: np.ndarray) -> dict[str, float]:
    text = "".join(chr(int(x)) for x in raw_ascii.reshape(-1))
    tokens = [token.strip() for token in text.replace("\n", ",").split(",") if token.strip()]
    params: dict[str, float] = {}
    for idx in range(0, len(tokens) - 1, 2):
        key = tokens[idx]
        try:
            value = float(tokens[idx + 1])
        except ValueError:
            continue
        params[key] = value
    return params


def load_config_h5(input_path: str) -> SimulationConfig:
    path = Path(input_path)
    with h5py.File(path, "r") as h5:
        pop_sizes = _read_vector(h5, "/config/Net/INIT001/N", np.int64).astype(int).tolist()
        dt = _read_scalar(h5, "/config/Net/INIT002/dt", float)
        step_tot = _read_scalar(h5, "/config/Net/INIT002/step_tot", int)

        populations: list[PopulationConfig] = []
        for pop_index, pop_size in enumerate(pop_sizes):
            pop_cfg = PopulationConfig(index=pop_index, size=pop_size)
            pop_root = f"/config/pops/pop{pop_index}"

            para_path = f"{pop_root}/PARA001/para_str_ascii"
            if _has_path(h5, para_path):
                pop_cfg.params = _parse_para_ascii(_read_vector(h5, para_path, np.int64))

            seed_path = f"{pop_root}/SEED001/seed"
            if _has_path(h5, seed_path):
                pop_cfg.seed = _read_scalar(h5, seed_path, int)

            init011_root = f"{pop_root}/INIT011"
            if _has_path(h5, f"{init011_root}/r_V0") and _has_path(h5, f"{init011_root}/p_fire"):
                pop_cfg.init_r_v0 = _read_scalar(h5, f"{init011_root}/r_V0", float)
                pop_cfg.init_p_fire = _read_scalar(h5, f"{init011_root}/p_fire", float)
            else:
                init003_path = f"{pop_root}/INIT003/p_fire"
                if _has_path(h5, init003_path):
                    pop_cfg.init_r_v0 = 1.0
                    pop_cfg.init_p_fire = _read_scalar(h5, init003_path, float)

            initv_path = f"{pop_root}/SETINITV/external_init_V"
            if _has_path(h5, initv_path):
                pop_cfg.init_v_external = _read_vector(h5, initv_path, np.float64)

            populations.append(pop_cfg)

        synapses: list[SynapseConfig] = []
        if _has_path(h5, "/config/syns/n_syns"):
            n_syns = _read_scalar(h5, "/config/syns/n_syns", int)
            for syn_index in range(n_syns):
                syn_root = f"/config/syns/syn{syn_index}"
                init006_root = f"{syn_root}/INIT006"
                if not _has_path(h5, f"{init006_root}/type"):
                    continue

                synapses.append(
                    SynapseConfig(
                        index=syn_index,
                        syn_type=_read_scalar(h5, f"{init006_root}/type", int),
                        pop_pre=_read_scalar(h5, f"{init006_root}/i_pre", int),
                        pop_post=_read_scalar(h5, f"{init006_root}/j_post", int),
                        i=_read_vector(h5, f"{init006_root}/I", np.int64),
                        j=_read_vector(h5, f"{init006_root}/J", np.int64),
                        k=_read_vector(h5, f"{init006_root}/K", np.float64),
                        d=_read_vector(h5, f"{init006_root}/D", np.float64),
                    )
                )

    return SimulationConfig(
        input_path=str(path),
        dt=dt,
        step_tot=step_tot,
        pop_sizes=pop_sizes,
        populations=populations,
        synapses=synapses,
    )

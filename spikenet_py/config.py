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
    is_restart: bool = False
    restart_state: "RestartState | None" = None


@dataclass
class PopulationRestartState:
    v: np.ndarray
    ref_step_left: np.ndarray


@dataclass
class SynapseRestartState:
    gs_sum: np.ndarray | None = None
    d_gs_sum_buffer: np.ndarray | None = None
    s_pre: np.ndarray | None = None
    trans_left: np.ndarray | None = None


@dataclass
class RestartState:
    populations: dict[int, PopulationRestartState] = field(default_factory=dict)
    synapses: dict[int, SynapseRestartState] = field(default_factory=dict)


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


def _read_matrix(h5: h5py.File, path: str, dtype: np.dtype) -> np.ndarray:
    if not _has_path(h5, path):
        raise KeyError(f"Missing HDF5 path: {path}")
    arr = np.asarray(h5[path][()])
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return arr.astype(dtype)


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


def _load_standard_config_h5(path: Path, h5: h5py.File) -> SimulationConfig:
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
        is_restart=False,
        restart_state=None,
    )


def _restart_edges_from_matrices(h5: h5py.File, syn_root: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    c_mat = _read_matrix(h5, f"{syn_root}/C", np.int64)
    d_mat = _read_matrix(h5, f"{syn_root}/D", np.float64)
    k_mat = _read_matrix(h5, f"{syn_root}/K", np.float64)

    i_list: list[int] = []
    j_list: list[int] = []
    k_list: list[float] = []
    d_list: list[float] = []

    for i_pre in range(c_mat.shape[0]):
        for edge_ind in range(c_mat.shape[1]):
            j_post = int(c_mat[i_pre, edge_ind])
            if j_post < 0:
                break
            i_list.append(i_pre)
            j_list.append(j_post)
            k_list.append(float(k_mat[i_pre, edge_ind]))
            d_list.append(float(d_mat[i_pre, edge_ind]))

    return (
        np.asarray(i_list, dtype=np.int64),
        np.asarray(j_list, dtype=np.int64),
        np.asarray(k_list, dtype=np.float64),
        np.asarray(d_list, dtype=np.float64),
    )


def _load_restart_config_h5(path: Path, h5: h5py.File) -> SimulationConfig:
    pop_sizes = _read_vector(h5, "/Net/N_array", np.int64).astype(int).tolist()
    dt = _read_scalar(h5, "/Net/dt", float)
    step_tot = _read_scalar(h5, "/Net/step_tot", int)

    restart_state = RestartState()
    populations: list[PopulationConfig] = []
    for pop_index, pop_size in enumerate(pop_sizes):
        pop_root = f"/pops/pop{pop_index}"
        params = {
            "Cm": _read_scalar(h5, f"{pop_root}/Cm", float, 0.25),
            "tau_ref": _read_scalar(h5, f"{pop_root}/tau_ref", float, 2.0),
            "V_rt": _read_scalar(h5, f"{pop_root}/V_rt", float, -60.0),
            "V_lk": _read_scalar(h5, f"{pop_root}/V_lk", float, -70.0),
            "V_th": _read_scalar(h5, f"{pop_root}/V_th", float, -50.0),
            "g_lk": _read_scalar(h5, f"{pop_root}/g_lk", float, 0.0167),
        }
        seed = _read_scalar(h5, f"{pop_root}/my_seed", int) if _has_path(h5, f"{pop_root}/my_seed") else None
        populations.append(PopulationConfig(index=pop_index, size=pop_size, params=params, seed=seed))

        restart_state.populations[pop_index] = PopulationRestartState(
            v=_read_vector(h5, f"{pop_root}/V", np.float64),
            ref_step_left=_read_vector(h5, f"{pop_root}/ref_step_left", np.int64),
        )

    synapses: list[SynapseConfig] = []
    if _has_path(h5, "/syns/n_syns"):
        n_syns = _read_scalar(h5, "/syns/n_syns", int)
        for syn_index in range(n_syns):
            syn_root = f"/syns/syn{syn_index}"
            syn_type = _read_scalar(h5, f"{syn_root}/syn_type", int)
            pop_pre = _read_scalar(h5, f"{syn_root}/pop_ind_pre", int)
            pop_post = _read_scalar(h5, f"{syn_root}/pop_ind_post", int)

            if _has_path(h5, f"{syn_root}/I") and _has_path(h5, f"{syn_root}/J") and _has_path(h5, f"{syn_root}/K") and _has_path(h5, f"{syn_root}/D"):
                i_vec = _read_vector(h5, f"{syn_root}/I", np.int64)
                j_vec = _read_vector(h5, f"{syn_root}/J", np.int64)
                k_vec = _read_vector(h5, f"{syn_root}/K", np.float64)
                d_vec = _read_vector(h5, f"{syn_root}/D", np.float64)
            else:
                i_vec, j_vec, k_vec, d_vec = _restart_edges_from_matrices(h5, syn_root)

            synapses.append(
                SynapseConfig(
                    index=syn_index,
                    syn_type=syn_type,
                    pop_pre=pop_pre,
                    pop_post=pop_post,
                    i=i_vec,
                    j=j_vec,
                    k=k_vec,
                    d=d_vec,
                )
            )

            syn_restart = SynapseRestartState()
            if _has_path(h5, f"{syn_root}/gs_sum"):
                syn_restart.gs_sum = _read_vector(h5, f"{syn_root}/gs_sum", np.float64)
            if _has_path(h5, f"{syn_root}/Gsm_0/d_gs_sum_buffer"):
                syn_restart.d_gs_sum_buffer = _read_matrix(h5, f"{syn_root}/Gsm_0/d_gs_sum_buffer", np.float64)
            if _has_path(h5, f"{syn_root}/Gsm_0/s"):
                syn_restart.s_pre = _read_vector(h5, f"{syn_root}/Gsm_0/s", np.float64)
            if _has_path(h5, f"{syn_root}/Gsm_0/trans_left"):
                syn_restart.trans_left = _read_vector(h5, f"{syn_root}/Gsm_0/trans_left", np.int64)

            if (
                syn_restart.gs_sum is not None
                or syn_restart.d_gs_sum_buffer is not None
                or syn_restart.s_pre is not None
                or syn_restart.trans_left is not None
            ):
                restart_state.synapses[syn_index] = syn_restart

    return SimulationConfig(
        input_path=str(path),
        dt=dt,
        step_tot=step_tot,
        pop_sizes=pop_sizes,
        populations=populations,
        synapses=synapses,
        is_restart=True,
        restart_state=restart_state,
    )


def load_config_h5(input_path: str) -> SimulationConfig:
    path = Path(input_path)
    with h5py.File(path, "r") as h5:
        if _has_path(h5, "/Net/N_array"):
            return _load_restart_config_h5(path, h5)
        return _load_standard_config_h5(path, h5)

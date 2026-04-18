from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import h5py
import numpy as np


@dataclass
class CommandResult:
    engine: str
    case_name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    output_file: Path | None
    run_dir: Path
    real_time_s: float | None = None
    user_time_s: float | None = None
    sys_time_s: float | None = None
    torch_cpu_time_ms: float | None = None
    torch_gpu_time_ms: float | None = None


@dataclass
class CheckItem:
    case_name: str
    path: str
    status: str
    detail: str
    max_abs: float | None = None
    max_rel: float | None = None


def _write_basic_case(case_path: Path, pop_sizes: list[int], dt: float, step_tot: int) -> None:
    with h5py.File(case_path, "w") as h5:
        h5.create_dataset("/config/Net/INIT001/N", data=np.asarray(pop_sizes, dtype=np.int32))
        h5.create_dataset("/config/Net/INIT002/dt", data=np.asarray([dt], dtype=np.float64))
        h5.create_dataset("/config/Net/INIT002/step_tot", data=np.asarray([step_tot], dtype=np.int32))
        for pop_index in range(len(pop_sizes)):
            h5.create_group(f"/config/pops/pop{pop_index}/SAMP003")


def _add_setinitv(case_path: Path, pop_index: int, values: np.ndarray) -> None:
    with h5py.File(case_path, "a") as h5:
        h5.create_dataset(
            f"/config/pops/pop{pop_index}/SETINITV/external_init_V",
            data=np.asarray(values, dtype=np.float64),
        )


def _add_synapses(case_path: Path, synapses: list[dict[str, Any]]) -> None:
    with h5py.File(case_path, "a") as h5:
        h5.create_dataset("/config/syns/n_syns", data=np.asarray([len(synapses)], dtype=np.int32))
        for idx, syn in enumerate(synapses):
            root = f"/config/syns/syn{idx}/INIT006"
            h5.create_dataset(f"{root}/type", data=np.asarray([syn["type"]], dtype=np.int32))
            h5.create_dataset(f"{root}/i_pre", data=np.asarray([syn["i_pre"]], dtype=np.int32))
            h5.create_dataset(f"{root}/j_post", data=np.asarray([syn["j_post"]], dtype=np.int32))
            h5.create_dataset(f"{root}/I", data=np.asarray(syn["I"], dtype=np.int32))
            h5.create_dataset(f"{root}/J", data=np.asarray(syn["J"], dtype=np.int32))
            h5.create_dataset(f"{root}/K", data=np.asarray(syn["K"], dtype=np.float64))
            h5.create_dataset(f"{root}/D", data=np.asarray(syn["D"], dtype=np.float64))
            h5.create_group(f"/config/syns/syn{idx}/SAMP004")


def _generate_scaled_synapse(
    rng: np.random.Generator,
    n_pre: int,
    n_post: int,
    edge_count: int,
    syn_type: int,
    i_pre: int,
    j_post: int,
) -> dict[str, Any]:
    i_arr = rng.integers(0, n_pre, size=edge_count, dtype=np.int32)
    j_arr = rng.integers(0, n_post, size=edge_count, dtype=np.int32)
    if syn_type == 0:
        k_arr = rng.uniform(0.015, 0.035, size=edge_count).astype(np.float64)
    elif syn_type == 1:
        k_arr = rng.uniform(0.010, 0.025, size=edge_count).astype(np.float64)
    else:
        k_arr = rng.uniform(0.010, 0.030, size=edge_count).astype(np.float64)
    d_arr = rng.uniform(0.1, 1.2, size=edge_count).astype(np.float64)
    return {
        "type": syn_type,
        "i_pre": i_pre,
        "j_post": j_post,
        "I": i_arr,
        "J": j_arr,
        "K": k_arr,
        "D": d_arr,
    }


def generate_cases(case_root: Path, case_scale: str = "small") -> list[Path]:
    case_root.mkdir(parents=True, exist_ok=True)
    cases: list[Path] = []

    if case_scale not in {"small", "medium", "large"}:
        raise ValueError(f"Unsupported case_scale: {case_scale}")

    if case_scale == "small":
        # Case 1: deterministic single-pop, no synapses.
        case1 = case_root / "0001-core-nosyn_in.h5"
        _write_basic_case(case1, pop_sizes=[12], dt=0.1, step_tot=120)
        init_v = np.full((12,), -60.0)
        init_v[0:3] = -49.0
        _add_setinitv(case1, pop_index=0, values=init_v)
        cases.append(case1)

        # Case 2: deterministic single-pop recurrent AMPA with delays.
        case2 = case_root / "0002-core-recurrent_in.h5"
        _write_basic_case(case2, pop_sizes=[10], dt=0.1, step_tot=140)
        init_v2 = np.full((10,), -62.0)
        init_v2[0:2] = -49.0
        _add_setinitv(case2, pop_index=0, values=init_v2)
        _add_synapses(
            case2,
            synapses=[
                {
                    "type": 0,
                    "i_pre": 0,
                    "j_post": 0,
                    "I": [0, 1, 2, 3, 4],
                    "J": [2, 3, 4, 5, 6],
                    "K": [0.03, 0.025, 0.02, 0.02, 0.02],
                    "D": [0.1, 0.2, 0.2, 0.3, 0.4],
                }
            ],
        )
        cases.append(case2)

        # Case 3: deterministic two-pop AMPA + GABA.
        case3 = case_root / "0003-core-twopop_in.h5"
        _write_basic_case(case3, pop_sizes=[8, 6], dt=0.1, step_tot=140)
        init_v3_p0 = np.full((8,), -62.0)
        init_v3_p1 = np.full((6,), -62.0)
        init_v3_p0[0:2] = -49.0
        _add_setinitv(case3, pop_index=0, values=init_v3_p0)
        _add_setinitv(case3, pop_index=1, values=init_v3_p1)
        _add_synapses(
            case3,
            synapses=[
                {
                    "type": 0,
                    "i_pre": 0,
                    "j_post": 1,
                    "I": [0, 1, 1, 2],
                    "J": [0, 1, 2, 3],
                    "K": [0.03, 0.03, 0.025, 0.02],
                    "D": [0.1, 0.1, 0.2, 0.2],
                },
                {
                    "type": 1,
                    "i_pre": 1,
                    "j_post": 0,
                    "I": [0, 1, 2],
                    "J": [0, 2, 4],
                    "K": [0.02, 0.02, 0.02],
                    "D": [0.2, 0.2, 0.3],
                },
            ],
        )
        cases.append(case3)
        return cases

    scale_cfg = {
        "medium": {
            "seed": 101,
            "dt": 0.1,
            "case1_n": 1024,
            "case1_steps": 1000,
            "case2_n": 896,
            "case2_steps": 1200,
            "case2_edges": 70000,
            "case3_n0": 768,
            "case3_n1": 768,
            "case3_steps": 1200,
            "case3_edges_01": 60000,
            "case3_edges_10": 60000,
            "hot_n": 16,
        },
        "large": {
            "seed": 202,
            "dt": 0.1,
            "case1_n": 2048,
            "case1_steps": 1500,
            "case2_n": 1792,
            "case2_steps": 1800,
            "case2_edges": 180000,
            "case3_n0": 1536,
            "case3_n1": 1536,
            "case3_steps": 1800,
            "case3_edges_01": 160000,
            "case3_edges_10": 160000,
            "hot_n": 32,
        },
    }[case_scale]
    rng = np.random.default_rng(scale_cfg["seed"])

    case1 = case_root / f"0001-core-nosyn-{case_scale}_in.h5"
    _write_basic_case(
        case1,
        pop_sizes=[int(scale_cfg["case1_n"])],
        dt=float(scale_cfg["dt"]),
        step_tot=int(scale_cfg["case1_steps"]),
    )
    init_v = np.full((int(scale_cfg["case1_n"]),), -62.0, dtype=np.float64)
    init_v[: int(scale_cfg["hot_n"])] = -49.0
    _add_setinitv(case1, pop_index=0, values=init_v)
    cases.append(case1)

    case2 = case_root / f"0002-core-recurrent-{case_scale}_in.h5"
    _write_basic_case(
        case2,
        pop_sizes=[int(scale_cfg["case2_n"])],
        dt=float(scale_cfg["dt"]),
        step_tot=int(scale_cfg["case2_steps"]),
    )
    init_v2 = np.full((int(scale_cfg["case2_n"]),), -62.0, dtype=np.float64)
    init_v2[: int(scale_cfg["hot_n"])] = -49.0
    _add_setinitv(case2, pop_index=0, values=init_v2)
    _add_synapses(
        case2,
        synapses=[
            _generate_scaled_synapse(
                rng=rng,
                n_pre=int(scale_cfg["case2_n"]),
                n_post=int(scale_cfg["case2_n"]),
                edge_count=int(scale_cfg["case2_edges"]),
                syn_type=0,
                i_pre=0,
                j_post=0,
            )
        ],
    )
    cases.append(case2)

    case3 = case_root / f"0003-core-twopop-{case_scale}_in.h5"
    _write_basic_case(
        case3,
        pop_sizes=[int(scale_cfg["case3_n0"]), int(scale_cfg["case3_n1"])],
        dt=float(scale_cfg["dt"]),
        step_tot=int(scale_cfg["case3_steps"]),
    )
    init_v3_p0 = np.full((int(scale_cfg["case3_n0"]),), -62.0, dtype=np.float64)
    init_v3_p1 = np.full((int(scale_cfg["case3_n1"]),), -62.0, dtype=np.float64)
    init_v3_p0[: int(scale_cfg["hot_n"])] = -49.0
    _add_setinitv(case3, pop_index=0, values=init_v3_p0)
    _add_setinitv(case3, pop_index=1, values=init_v3_p1)
    _add_synapses(
        case3,
        synapses=[
            _generate_scaled_synapse(
                rng=rng,
                n_pre=int(scale_cfg["case3_n0"]),
                n_post=int(scale_cfg["case3_n1"]),
                edge_count=int(scale_cfg["case3_edges_01"]),
                syn_type=0,
                i_pre=0,
                j_post=1,
            ),
            _generate_scaled_synapse(
                rng=rng,
                n_pre=int(scale_cfg["case3_n1"]),
                n_post=int(scale_cfg["case3_n0"]),
                edge_count=int(scale_cfg["case3_edges_10"]),
                syn_type=1,
                i_pre=1,
                j_post=0,
            ),
        ],
    )
    cases.append(case3)

    return cases


def _run_command(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    time_file: Path | None = None,
) -> tuple[int, str, str]:
    wrapped_command = command
    time_bin = shutil.which("time")
    if time_file is not None and time_bin is not None:
        wrapped_command = [time_bin, "-f", "real=%e\\nuser=%U\\nsys=%S", "-o", str(time_file), *command]

    proc = subprocess.run(wrapped_command, cwd=str(cwd), env=env, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _parse_time_metrics(time_file: Path) -> tuple[float | None, float | None, float | None]:
    if not time_file.exists():
        return None, None, None

    real_s: float | None = None
    user_s: float | None = None
    sys_s: float | None = None
    for line in time_file.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        try:
            parsed = float(value.strip())
        except ValueError:
            continue
        if key == "real":
            real_s = parsed
        elif key == "user":
            user_s = parsed
        elif key == "sys":
            sys_s = parsed
    return real_s, user_s, sys_s


def _parse_torch_profile(profile_file: Path) -> tuple[float | None, float | None]:
    if not profile_file.exists():
        return None, None
    try:
        payload = json.loads(profile_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, None

    cpu_ms = payload.get("torch_cpu_time_ms")
    gpu_ms = payload.get("torch_gpu_time_ms")
    try:
        cpu_ms = float(cpu_ms) if cpu_ms is not None else None
    except (TypeError, ValueError):
        cpu_ms = None
    try:
        gpu_ms = float(gpu_ms) if gpu_ms is not None else None
    except (TypeError, ValueError):
        gpu_ms = None
    return cpu_ms, gpu_ms


def run_engine_for_case(
    engine: str,
    case_file: Path,
    run_root: Path,
    repo_root: Path,
    cpp_simulator: Path,
    python_exe: str,
    python_device: str,
) -> CommandResult:
    run_dir = run_root / engine / case_file.stem
    run_dir.mkdir(parents=True, exist_ok=True)

    local_input = run_dir / case_file.name
    shutil.copy2(case_file, local_input)

    if engine == "cpp":
        command = [str(cpp_simulator), local_input.name]
        env = os.environ.copy()
        profile_file: Path | None = None
    else:
        command = [python_exe, "-m", "spikenet_py.cli", local_input.name, "--device", python_device]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)
        profile_file = run_dir / "torch_profile.json"
        env["SPIKENET_TORCH_PROFILE_JSON"] = str(profile_file)

    time_file = run_dir / "runtime_metrics.txt"
    returncode, stdout, stderr = _run_command(command, cwd=run_dir, env=env, time_file=time_file)
    out_files = sorted(run_dir.glob("*_out.h5"), key=lambda p: p.stat().st_mtime)
    output_file = out_files[-1] if out_files else None

    real_s, user_s, sys_s = _parse_time_metrics(time_file)
    torch_cpu_ms, torch_gpu_ms = (None, None)
    if profile_file is not None:
        torch_cpu_ms, torch_gpu_ms = _parse_torch_profile(profile_file)

    return CommandResult(
        engine=engine,
        case_name=case_file.stem,
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        output_file=output_file,
        run_dir=run_dir,
        real_time_s=real_s,
        user_time_s=user_s,
        sys_time_s=sys_s,
        torch_cpu_time_ms=torch_cpu_ms,
        torch_gpu_time_ms=torch_gpu_ms,
    )


def _allclose_with_metrics(a: np.ndarray, b: np.ndarray, rtol: float, atol: float) -> tuple[bool, float, float]:
    a64 = np.asarray(a, dtype=np.float64)
    b64 = np.asarray(b, dtype=np.float64)
    diff = np.abs(a64 - b64)
    max_abs = float(np.max(diff)) if diff.size > 0 else 0.0
    denom = np.maximum(np.abs(a64), np.abs(b64))
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(denom > 0.0, diff / denom, 0.0)
    max_rel = float(np.max(rel)) if rel.size > 0 else 0.0
    ok = np.allclose(a64, b64, rtol=rtol, atol=atol)
    return ok, max_abs, max_rel


def _read_dataset(h5: h5py.File, path: str) -> np.ndarray:
    data = h5[path][()]
    arr = np.asarray(data)
    if arr.dtype.kind in {"S", "U", "O"}:
        return arr.astype(str)
    return arr


def compare_outputs(
    case_name: str,
    cpp_out: Path,
    py_out: Path,
    rtol: float,
    atol: float,
) -> list[CheckItem]:
    checks: list[CheckItem] = []

    with h5py.File(cpp_out, "r") as h5_cpp, h5py.File(py_out, "r") as h5_py:
        required_paths = [
            "/config_filename/config_filename",
            "/run_away_killed/step",
        ]

        for path in required_paths:
            in_cpp = path in h5_cpp
            in_py = path in h5_py
            if in_cpp and in_py:
                checks.append(CheckItem(case_name, path, "PASS", "present in both outputs"))
            else:
                checks.append(
                    CheckItem(
                        case_name,
                        path,
                        "FAIL",
                        f"presence mismatch: cpp={in_cpp}, py={in_py}",
                    )
                )

        # Compare population and synapse groups by intersection.
        pop_groups_cpp = sorted([k for k in h5_cpp.keys() if k.startswith("pop_result_")])
        pop_groups_py = sorted([k for k in h5_py.keys() if k.startswith("pop_result_")])
        pop_groups = sorted(set(pop_groups_cpp).intersection(pop_groups_py))

        syn_groups_cpp = sorted([k for k in h5_cpp.keys() if k.startswith("syn_result_")])
        syn_groups_py = sorted([k for k in h5_py.keys() if k.startswith("syn_result_")])
        syn_groups = sorted(set(syn_groups_cpp).intersection(syn_groups_py))

        pop_paths = [
            "spike_hist_tot",
            "num_spikes_pop",
            "num_ref_pop",
            "stats_V_mean",
            "stats_V_std",
            "stats_I_input_mean",
            "stats_I_input_std",
        ]

        for group in pop_groups:
            for rel_path in pop_paths:
                p = f"/{group}/{rel_path}"
                if p not in h5_cpp or p not in h5_py:
                    checks.append(CheckItem(case_name, p, "FAIL", "dataset missing in one output"))
                    continue
                a = _read_dataset(h5_cpp, p)
                b = _read_dataset(h5_py, p)
                if a.shape != b.shape:
                    checks.append(
                        CheckItem(case_name, p, "FAIL", f"shape mismatch: cpp={a.shape}, py={b.shape}")
                    )
                    continue
                if np.issubdtype(a.dtype, np.integer):
                    ok = np.array_equal(a, b)
                    checks.append(
                        CheckItem(
                            case_name,
                            p,
                            "PASS" if ok else "FAIL",
                            "integer exact match" if ok else "integer values differ",
                        )
                    )
                else:
                    ok, max_abs, max_rel = _allclose_with_metrics(a, b, rtol=rtol, atol=atol)
                    checks.append(
                        CheckItem(
                            case_name,
                            p,
                            "PASS" if ok else "FAIL",
                            "allclose" if ok else "allclose failed",
                            max_abs=max_abs,
                            max_rel=max_rel,
                        )
                    )

        syn_paths = ["stats_I_mean"]
        for group in syn_groups:
            for rel_path in syn_paths:
                p = f"/{group}/{rel_path}"
                if p not in h5_cpp or p not in h5_py:
                    checks.append(CheckItem(case_name, p, "FAIL", "dataset missing in one output"))
                    continue
                a = _read_dataset(h5_cpp, p)
                b = _read_dataset(h5_py, p)
                if a.shape != b.shape:
                    checks.append(
                        CheckItem(case_name, p, "FAIL", f"shape mismatch: cpp={a.shape}, py={b.shape}")
                    )
                    continue
                ok, max_abs, max_rel = _allclose_with_metrics(a, b, rtol=rtol, atol=atol)
                checks.append(
                    CheckItem(
                        case_name,
                        p,
                        "PASS" if ok else "FAIL",
                        "allclose" if ok else "allclose failed",
                        max_abs=max_abs,
                        max_rel=max_rel,
                    )
                )

    return checks


def compare_cli_signature(cpp_result: CommandResult, py_result: CommandResult) -> list[CheckItem]:
    checks: list[CheckItem] = []
    required_tokens = [
        "Number of input files:",
        "Processing input file No.1 out of 1...",
        "Data file name is:",
        "The planet earth is blue and there's nothing I can do.",
    ]

    for token in required_tokens:
        cpp_has = token in cpp_result.stdout
        py_has = token in py_result.stdout
        status = "PASS" if (cpp_has and py_has) else "FAIL"
        checks.append(
            CheckItem(
                case_name=cpp_result.case_name,
                path=f"CLI::{token}",
                status=status,
                detail=f"cpp={cpp_has}, py={py_has}",
            )
        )

    checks.append(
        CheckItem(
            case_name=cpp_result.case_name,
            path="CLI::exit_code",
            status="PASS" if (cpp_result.returncode == 0 and py_result.returncode == 0) else "FAIL",
            detail=f"cpp={cpp_result.returncode}, py={py_result.returncode}",
        )
    )

    return checks


def render_markdown_report(
    report_path: Path,
    checks: list[CheckItem],
    cpp_results: list[CommandResult],
    py_results: list[CommandResult],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(checks)
    failed = len([c for c in checks if c.status == "FAIL"])
    passed = total - failed

    lines: list[str] = []
    lines.append("# SpikeNet C++ vs Python Equivalence Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Total checks: {total}")
    lines.append(f"- Passed: {passed}")
    lines.append(f"- Failed: {failed}")
    lines.append("")

    cpp_real_total = sum(r.real_time_s for r in cpp_results if r.real_time_s is not None)
    cpp_user_total = sum(r.user_time_s for r in cpp_results if r.user_time_s is not None)
    py_real_total = sum(r.real_time_s for r in py_results if r.real_time_s is not None)
    py_user_total = sum(r.user_time_s for r in py_results if r.user_time_s is not None)
    py_torch_cpu_total = sum(r.torch_cpu_time_ms for r in py_results if r.torch_cpu_time_ms is not None)
    py_torch_gpu_total = sum(r.torch_gpu_time_ms for r in py_results if r.torch_gpu_time_ms is not None)

    lines.append("## Performance Summary")
    lines.append("")
    lines.append("| Engine | Real Time Total (s) | User Time Total (s) | Torch CPU Time Total (ms) | Torch GPU Time Total (ms) |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(f"| C++ | {cpp_real_total:.3f} | {cpp_user_total:.3f} | N/A | N/A |")
    lines.append(f"| Torch | {py_real_total:.3f} | {py_user_total:.3f} | {py_torch_cpu_total:.3f} | {py_torch_gpu_total:.3f} |")
    lines.append("")

    lines.append("## Executions")
    lines.append("")
    lines.append("| Engine | Case | Return Code | Real (s) | User (s) | Sys (s) | Torch CPU (ms) | Torch GPU (ms) | Output File |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for r in cpp_results + py_results:
        real_s = "" if r.real_time_s is None else f"{r.real_time_s:.3f}"
        user_s = "" if r.user_time_s is None else f"{r.user_time_s:.3f}"
        sys_s = "" if r.sys_time_s is None else f"{r.sys_time_s:.3f}"
        torch_cpu_ms = "" if r.torch_cpu_time_ms is None else f"{r.torch_cpu_time_ms:.3f}"
        torch_gpu_ms = "" if r.torch_gpu_time_ms is None else f"{r.torch_gpu_time_ms:.3f}"
        lines.append(
            f"| {r.engine} | {r.case_name} | {r.returncode} | {real_s} | {user_s} | {sys_s} | {torch_cpu_ms} | {torch_gpu_ms} | {r.output_file} |"
        )

    lines.append("")
    lines.append("## Detailed Checks")
    lines.append("")
    lines.append("| Case | Path | Status | Detail | Max Abs | Max Rel |")
    lines.append("|---|---|---|---|---:|---:|")
    for c in checks:
        max_abs = "" if c.max_abs is None else f"{c.max_abs:.3e}"
        max_rel = "" if c.max_rel is None else f"{c.max_rel:.3e}"
        lines.append(f"| {c.case_name} | {c.path} | {c.status} | {c.detail} | {max_abs} | {max_rel} |")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def render_json_report(
    report_path: Path,
    checks: list[CheckItem],
    cpp_results: list[CommandResult],
    py_results: list[CommandResult],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    cpp_real_total = sum(r.real_time_s for r in cpp_results if r.real_time_s is not None)
    cpp_user_total = sum(r.user_time_s for r in cpp_results if r.user_time_s is not None)
    py_real_total = sum(r.real_time_s for r in py_results if r.real_time_s is not None)
    py_user_total = sum(r.user_time_s for r in py_results if r.user_time_s is not None)
    py_torch_cpu_total = sum(r.torch_cpu_time_ms for r in py_results if r.torch_cpu_time_ms is not None)
    py_torch_gpu_total = sum(r.torch_gpu_time_ms for r in py_results if r.torch_gpu_time_ms is not None)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": len(checks),
            "failed": len([c for c in checks if c.status == "FAIL"]),
            "passed": len([c for c in checks if c.status == "PASS"]),
        },
        "performance_summary": {
            "cpp": {
                "real_time_total_s": cpp_real_total,
                "user_time_total_s": cpp_user_total,
            },
            "torch": {
                "real_time_total_s": py_real_total,
                "user_time_total_s": py_user_total,
                "torch_cpu_time_total_ms": py_torch_cpu_total,
                "torch_gpu_time_total_ms": py_torch_gpu_total,
            },
        },
        "executions": [
            {
                "engine": r.engine,
                "case": r.case_name,
                "return_code": r.returncode,
                "real_time_s": r.real_time_s,
                "user_time_s": r.user_time_s,
                "sys_time_s": r.sys_time_s,
                "torch_cpu_time_ms": r.torch_cpu_time_ms,
                "torch_gpu_time_ms": r.torch_gpu_time_ms,
                "output_file": str(r.output_file) if r.output_file is not None else None,
            }
            for r in (cpp_results + py_results)
        ],
        "checks": [
            {
                "case": c.case_name,
                "path": c.path,
                "status": c.status,
                "detail": c.detail,
                "max_abs": c.max_abs,
                "max_rel": c.max_rel,
            }
            for c in checks
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run side-by-side equivalence checks between the original C++ simulator and the Python simulator."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cpp-simulator", type=Path, default=Path("simulator"))
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--workdir", type=Path, default=Path(".equivalence_runs"))
    parser.add_argument("--report-md", type=Path, default=Path("reports/equivalence/report.md"))
    parser.add_argument("--report-json", type=Path, default=Path("reports/equivalence/report.json"))
    parser.add_argument("--python-device", default="cpu", help="Torch device for Python simulator, e.g. cpu or cuda")
    parser.add_argument(
        "--case-scale",
        default="small",
        choices=["small", "medium", "large"],
        help="Synthetic case scale used for equivalence/performance runs",
    )
    parser.add_argument("--rtol", type=float, default=1e-7)
    parser.add_argument("--atol", type=float, default=1e-9)
    parser.add_argument("--keep-workdir", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()

    cpp_simulator = args.cpp_simulator
    if not cpp_simulator.is_absolute():
        cpp_simulator = (repo_root / cpp_simulator).resolve()

    if not cpp_simulator.exists():
        print(f"[ERROR] C++ simulator not found: {cpp_simulator}")
        print("Build it first (autoconf && ./configure && make) or pass --cpp-simulator.")
        return 2

    workdir = args.workdir
    if not workdir.is_absolute():
        workdir = (repo_root / workdir).resolve()

    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    case_root = workdir / "cases"
    cases = generate_cases(case_root, case_scale=args.case_scale)

    cpp_results: list[CommandResult] = []
    py_results: list[CommandResult] = []
    checks: list[CheckItem] = []

    for case_file in cases:
        cpp_res = run_engine_for_case(
            "cpp",
            case_file=case_file,
            run_root=workdir,
            repo_root=repo_root,
            cpp_simulator=cpp_simulator,
            python_exe=args.python_exe,
            python_device=args.python_device,
        )
        py_res = run_engine_for_case(
            "python",
            case_file=case_file,
            run_root=workdir,
            repo_root=repo_root,
            cpp_simulator=cpp_simulator,
            python_exe=args.python_exe,
            python_device=args.python_device,
        )

        cpp_results.append(cpp_res)
        py_results.append(py_res)

        checks.extend(compare_cli_signature(cpp_res, py_res))

        if cpp_res.output_file is None or py_res.output_file is None:
            checks.append(
                CheckItem(
                    case_name=case_file.stem,
                    path="OUTPUT::presence",
                    status="FAIL",
                    detail=f"cpp_out={cpp_res.output_file}, py_out={py_res.output_file}",
                )
            )
            continue

        checks.extend(
            compare_outputs(
                case_name=case_file.stem,
                cpp_out=cpp_res.output_file,
                py_out=py_res.output_file,
                rtol=args.rtol,
                atol=args.atol,
            )
        )

    report_md = args.report_md
    if not report_md.is_absolute():
        report_md = (repo_root / report_md).resolve()
    report_json = args.report_json
    if not report_json.is_absolute():
        report_json = (repo_root / report_json).resolve()

    render_markdown_report(report_md, checks, cpp_results, py_results)
    render_json_report(report_json, checks, cpp_results, py_results)

    failed = len([c for c in checks if c.status == "FAIL"])
    print(f"Equivalence checks complete. failed={failed}")
    print(f"Markdown report: {report_md}")
    print(f"JSON report: {report_json}")

    if not args.keep_workdir:
        shutil.rmtree(workdir)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def generate_cases(case_root: Path) -> list[Path]:
    case_root.mkdir(parents=True, exist_ok=True)
    cases: list[Path] = []

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


def _run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def run_engine_for_case(
    engine: str,
    case_file: Path,
    run_root: Path,
    repo_root: Path,
    cpp_simulator: Path,
    python_exe: str,
) -> CommandResult:
    run_dir = run_root / engine / case_file.stem
    run_dir.mkdir(parents=True, exist_ok=True)

    local_input = run_dir / case_file.name
    shutil.copy2(case_file, local_input)

    if engine == "cpp":
        command = [str(cpp_simulator), local_input.name]
        env = os.environ.copy()
    else:
        command = [python_exe, "-m", "spikenet_py.cli", local_input.name]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)

    returncode, stdout, stderr = _run_command(command, cwd=run_dir, env=env)
    out_files = sorted(run_dir.glob("*_out.h5"), key=lambda p: p.stat().st_mtime)
    output_file = out_files[-1] if out_files else None

    return CommandResult(
        engine=engine,
        case_name=case_file.stem,
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        output_file=output_file,
        run_dir=run_dir,
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

    lines.append("## Executions")
    lines.append("")
    lines.append("| Engine | Case | Return Code | Output File |")
    lines.append("|---|---|---:|---|")
    for r in cpp_results + py_results:
        lines.append(f"| {r.engine} | {r.case_name} | {r.returncode} | {r.output_file} |")

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


def render_json_report(report_path: Path, checks: list[CheckItem]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": len(checks),
            "failed": len([c for c in checks if c.status == "FAIL"]),
            "passed": len([c for c in checks if c.status == "PASS"]),
        },
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
    cases = generate_cases(case_root)

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
        )
        py_res = run_engine_for_case(
            "python",
            case_file=case_file,
            run_root=workdir,
            repo_root=repo_root,
            cpp_simulator=cpp_simulator,
            python_exe=args.python_exe,
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
    render_json_report(report_json, checks)

    failed = len([c for c in checks if c.status == "FAIL"])
    print(f"Equivalence checks complete. failed={failed}")
    print(f"Markdown report: {report_md}")
    print(f"JSON report: {report_json}")

    if not args.keep_workdir:
        shutil.rmtree(workdir)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

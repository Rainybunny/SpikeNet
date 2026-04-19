from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import h5py
import numpy as np


def make_minimal_input(path: Path) -> None:
    with h5py.File(path, "w") as h5:
        h5.create_dataset("/config/Net/INIT001/N", data=np.asarray([16], dtype=np.int32))
        h5.create_dataset("/config/Net/INIT002/dt", data=np.asarray([0.1], dtype=np.float64))
        h5.create_dataset("/config/Net/INIT002/step_tot", data=np.asarray([100], dtype=np.int32))

        h5.create_dataset("/config/pops/pop0/INIT011/r_V0", data=np.asarray([1.0], dtype=np.float64))
        h5.create_dataset("/config/pops/pop0/INIT011/p_fire", data=np.asarray([0.15], dtype=np.float64))
        h5.create_dataset("/config/pops/pop0/SAMP103/time_start", data=np.asarray([10], dtype=np.int32))
        h5.create_dataset("/config/pops/pop0/SAMP103/time_end", data=np.asarray([90], dtype=np.int32))
        h5.create_dataset("/config/pops/pop0/SAMP005/LFP_neurons", data=np.ones((16, 1), dtype=np.float64))

        h5.create_dataset("/config/syns/n_syns", data=np.asarray([1], dtype=np.int32))
        h5.create_dataset("/config/syns/syn0/INIT006/type", data=np.asarray([0], dtype=np.int32))
        h5.create_dataset("/config/syns/syn0/INIT006/i_pre", data=np.asarray([0], dtype=np.int32))
        h5.create_dataset("/config/syns/syn0/INIT006/j_post", data=np.asarray([0], dtype=np.int32))

        i = np.asarray([0, 1, 2, 3, 4, 5], dtype=np.int32)
        j = np.asarray([1, 2, 3, 4, 5, 6], dtype=np.int32)
        k = np.asarray([0.02, 0.02, 0.02, 0.02, 0.02, 0.02], dtype=np.float64)
        d = np.asarray([1.0, 1.0, 2.0, 2.0, 3.0, 3.0], dtype=np.float64)

        h5.create_dataset("/config/syns/syn0/INIT006/I", data=i)
        h5.create_dataset("/config/syns/syn0/INIT006/J", data=j)
        h5.create_dataset("/config/syns/syn0/INIT006/K", data=k)
        h5.create_dataset("/config/syns/syn0/INIT006/D", data=d)
        h5.create_dataset("/config/syns/syn0/SAMP104/time_start", data=np.asarray([10], dtype=np.int32))
        h5.create_dataset("/config/syns/syn0/SAMP104/time_end", data=np.asarray([90], dtype=np.int32))


def validate_output(path: Path, expect_extended_stats: bool) -> None:
    with h5py.File(path, "r") as h5:
        assert "/config_filename/config_filename" in h5
        assert "/run_away_killed/step" in h5
        assert "/pop_result_0/spike_hist_tot" in h5
        assert "/pop_result_0/num_spikes_pop" in h5
        assert "/syn_result_0/stats_I_mean" in h5

        if expect_extended_stats:
            v_cov = np.asarray(h5["/pop_result_0/stats_V_time_cov"][()])
            if v_cov.shape != (16, 16):
                raise RuntimeError(f"unexpected stats_V_time_cov shape: {v_cov.shape}")

            lfp_data = np.asarray(h5["/pop_result_0/LFP_data"][()])
            if lfp_data.shape[0] != 1 or lfp_data.shape[1] != 100:
                raise RuntimeError(f"unexpected LFP_data shape: {lfp_data.shape}")

            s_cov = np.asarray(h5["/syn_result_0/stats_s_time_cov"][()])
            if s_cov.shape != (16, 16):
                raise RuntimeError(f"unexpected stats_s_time_cov shape: {s_cov.shape}")


def validate_restart(path: Path) -> None:
    with h5py.File(path, "r") as h5:
        assert "/Net/N_array" in h5
        assert "/Net/dt" in h5
        assert "/Net/step_tot" in h5
        assert "/pops/pop0/V" in h5
        assert "/pops/pop0/ref_step_left" in h5
        assert "/syns/n_syns" in h5


def _run_cli(repo_root: Path, input_h5: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "spikenet_py.cli", str(input_h5)]
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    print(proc.stdout)
    return proc


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="spikenet_smoke_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        input_h5 = tmp_dir / "0001-smoke_in.h5"
        make_minimal_input(input_h5)

        proc = _run_cli(repo_root, input_h5)
        if proc.returncode != 0:
            print(proc.stderr)
            raise RuntimeError("smoke test run failed")

        out_files = sorted(tmp_dir.glob("*_out.h5"), key=lambda p: p.stat().st_mtime)
        if not out_files:
            raise RuntimeError("no output file generated")

        validate_output(out_files[-1], expect_extended_stats=True)

        restart_files = sorted(tmp_dir.glob("*_restart.h5"), key=lambda p: p.stat().st_mtime)
        if not restart_files:
            raise RuntimeError("no restart file generated")
        restart_file = restart_files[-1]
        validate_restart(restart_file)

        # Force a known post-restart state so the next run has deterministic first-step spikes.
        with h5py.File(restart_file, "a") as h5:
            h5["/pops/pop0/V"][...] = np.full((16,), -49.0, dtype=np.float64)
            h5["/pops/pop0/ref_step_left"][...] = np.zeros((16,), dtype=np.int32)

        proc_restart = _run_cli(repo_root, restart_file)
        if proc_restart.returncode != 0:
            print(proc_restart.stderr)
            raise RuntimeError("restart smoke test run failed")

        out_files_after_restart = sorted(tmp_dir.glob("*_out.h5"), key=lambda p: p.stat().st_mtime)
        if len(out_files_after_restart) < 2:
            raise RuntimeError("restart run did not generate a new output file")

        restart_out = out_files_after_restart[-1]
        validate_output(restart_out, expect_extended_stats=False)
        with h5py.File(restart_out, "r") as h5:
            first_step_spikes = int(np.asarray(h5["/pop_result_0/num_spikes_pop"][()]).reshape(-1)[0])
            if first_step_spikes != 16:
                raise RuntimeError(
                    f"restart state not applied as expected, first_step_spikes={first_step_spikes}, expected=16"
                )

        print(f"Smoke test passed (base): {out_files[-1]}")
        print(f"Smoke test passed (restart): {restart_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

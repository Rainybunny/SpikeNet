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


def validate_output(path: Path) -> None:
    with h5py.File(path, "r") as h5:
        assert "/config_filename/config_filename" in h5
        assert "/run_away_killed/step" in h5
        assert "/pop_result_0/spike_hist_tot" in h5
        assert "/pop_result_0/num_spikes_pop" in h5
        assert "/syn_result_0/stats_I_mean" in h5


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="spikenet_smoke_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        input_h5 = tmp_dir / "0001-smoke_in.h5"
        make_minimal_input(input_h5)

        cmd = [sys.executable, "-m", "spikenet_py.cli", str(input_h5)]
        proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr)
            raise RuntimeError("smoke test run failed")

        out_files = list(tmp_dir.glob("*_out.h5"))
        if not out_files:
            raise RuntimeError("no output file generated")

        validate_output(out_files[0])
        print(f"Smoke test passed: {out_files[0]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

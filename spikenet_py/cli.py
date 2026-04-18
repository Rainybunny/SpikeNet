from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run_single_file


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SpikeNet Python simulator (migration scaffold)")
    parser.add_argument("input_files", nargs="+", help="Input HDF5 configuration files")
    parser.add_argument("--device", default="cpu", help="Torch device, e.g. cpu or cuda")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    print(f"Number of input files: {len(args.input_files)}")
    had_error = False

    for idx, input_file in enumerate(args.input_files, start=1):
        print(f"Processing input file No.{idx} out of {len(args.input_files)}...")
        path = Path(input_file)

        if path.suffix.lower() != ".h5":
            print("Unrecognized input filename extension.")
            had_error = True
            continue

        if "restart" in path.name:
            print("Restart input is not implemented yet in the Python migration scaffold.")
            had_error = True
            continue

        try:
            out_stem, _ = run_single_file(str(path), device=args.device)
            print(f"Input file No.{idx} out of {len(args.input_files)} processed.")
            print("Data file name is:")
            print(f"\t{out_stem}")
            print("------------------------------------------------------------")
        except Exception as exc:  # pragma: no cover
            had_error = True
            print(f"Failed to process {input_file}: {exc}")

    print("The planet earth is blue and there's nothing I can do.")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())

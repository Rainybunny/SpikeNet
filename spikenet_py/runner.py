from __future__ import annotations

import time
from pathlib import Path

import h5py
import numpy as np
import torch

from .config import SimulationConfig, load_config_h5
from .core import Population, Synapse


def _generate_output_stem(input_path: str) -> str:
    in_path = Path(input_path)
    stem = in_path.with_suffix("")
    timestamp_ms = int(time.time() * 1000)
    return f"{stem}_{timestamp_ms}"


class SimulationRunner:
    def __init__(self, config: SimulationConfig, device: str = "cpu") -> None:
        self.config = config
        self.device = torch.device(device)

        self.populations = [
            Population(cfg=pop_cfg, dt=config.dt, step_tot=config.step_tot, device=self.device)
            for pop_cfg in config.populations
        ]
        self.synapses = [
            Synapse(
                cfg=syn_cfg,
                dt=config.dt,
                n_pre=config.pop_sizes[syn_cfg.pop_pre],
                n_post=config.pop_sizes[syn_cfg.pop_post],
                device=self.device,
            )
            for syn_cfg in config.synapses
            if 0 <= syn_cfg.pop_pre < len(config.pop_sizes) and syn_cfg.pop_post < len(config.pop_sizes)
        ]

    def simulate(self) -> None:
        for step_current in range(self.config.step_tot):
            for population in self.populations:
                population.update_spikes(step_current)

            for synapse in self.synapses:
                synapse.update(step_current, self.populations)

            for population in self.populations:
                population.update_voltage(step_current)

    def write_output(self, input_path: str, out_stem: str) -> str:
        out_file = f"{out_stem}_out.h5"
        with h5py.File(out_file, "w") as h5:
            config_group = h5.create_group("/config_filename")
            config_group.create_dataset(
                "config_filename",
                data=np.asarray([input_path], dtype=h5py.string_dtype("utf-8")),
            )

            killed_group = h5.create_group("/run_away_killed")
            killed_group.create_dataset("step", data=np.asarray([-1], dtype=np.int32))

            for idx, population in enumerate(self.populations):
                pop_group = h5.create_group(f"/pop_result_{idx}")
                population.write_results(pop_group)

            for idx, synapse in enumerate(self.synapses):
                syn_group = h5.create_group(f"/syn_result_{idx}")
                synapse.write_results(syn_group)

        return out_file


def run_single_file(input_path: str, device: str = "cpu") -> tuple[str, str]:
    config = load_config_h5(input_path)
    runner = SimulationRunner(config=config, device=device)
    runner.simulate()

    out_stem = _generate_output_stem(input_path)
    out_file = runner.write_output(input_path=input_path, out_stem=out_stem)
    return out_stem, out_file
